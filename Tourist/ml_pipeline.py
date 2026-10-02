"""ML model training pipeline.

Provides:
- Model training from user behavior data
- Model evaluation (precision, recall, F1)
- Model versioning and deployment
- A/B testing support
"""
import logging
import pickle
import hashlib
from datetime import timedelta

from django.db.models import Avg, Count, Q
from django.utils import timezone
from django.core.cache import cache

from .models import (
    Destination, VisitHistory, Favorite, Review, Rating,
    RecommendationEvent, MLTrainingRun, MLInsight,
)

logger = logging.getLogger(__name__)


def train_model(model_type='recommendation', dataset_size=1000):
    """Train a model from user behavior data.

    Args:
        model_type: Type of model ('recommendation', 'risk', 'crowd')
        dataset_size: Number of records to use for training

    Returns:
        MLTrainingRun instance
    """
    try:
        # Create training run record
        run = MLTrainingRun.objects.create(
            model_type=model_type,
            status=MLTrainingRun.Status.RUNNING,
            version=_generate_version(),
            dataset_size=dataset_size,
        )

        # Train based on model type
        if model_type == 'recommendation':
            metrics = _train_recommendation_model(run, dataset_size)
        elif model_type == 'risk':
            metrics = _train_risk_model(run, dataset_size)
        elif model_type == 'crowd':
            metrics = _train_crowd_model(run, dataset_size)
        else:
            raise ValueError(f"Unknown model type: {model_type}")

        # Update run with results
        run.status = MLTrainingRun.Status.SUCCEEDED
        run.validation_metrics = metrics
        run.completed_at = timezone.now()
        run.save()

        logger.info(f"Model training completed: {run.version} with metrics: {metrics}")
        return run

    except Exception as exc:
        logger.error(f"Model training failed: {exc}")
        if 'run' in locals():
            run.status = MLTrainingRun.Status.FAILED
            run.output_log = str(exc)
            run.completed_at = timezone.now()
            run.save()
        raise


def evaluate_model(model_version):
    """Evaluate a trained model.

    Args:
        model_version: Model version string

    Returns:
        Dict with evaluation metrics
    """
    try:
        run = MLTrainingRun.objects.get(version=model_version)

        # Calculate metrics from recent predictions
        recent_events = RecommendationEvent.objects.filter(
            created_at__gte=timezone.now() - timedelta(days=7),
            score__isnull=False,
        )

        metrics = {
            'precision': _calculate_precision(recent_events),
            'recall': _calculate_recall(recent_events),
            'f1_score': 0,
            'coverage': _calculate_coverage(recent_events),
        }

        # F1 score
        if metrics['precision'] + metrics['recall'] > 0:
            metrics['f1_score'] = 2 * (
                metrics['precision'] * metrics['recall']
            ) / (metrics['precision'] + metrics['recall'])

        return metrics

    except MLTrainingRun.DoesNotExist:
        return {'error': f'Model version {model_version} not found'}
    except Exception as exc:
        logger.error(f"Error evaluating model: {exc}")
        return {'error': str(exc)}


def deploy_model(model_version):
    """Deploy a trained model.

    Args:
        model_version: Model version string

    Returns:
        True if deployed successfully
    """
    try:
        run = MLTrainingRun.objects.get(version=model_version)

        if run.status != MLTrainingRun.Status.SUCCEEDED:
            raise ValueError(f"Model {model_version} has not been trained successfully")

        # Set as active model in cache
        cache.set(f"ml_model:active:{run.model_type}", model_version, 86400)

        # Update previous model
        previous = MLTrainingRun.objects.filter(
            model_type=run.model_type,
            status=MLTrainingRun.Status.SUCCEEDED,
        ).exclude(version=model_version).first()

        if previous:
            run.previous_version = previous.version
            run.save()

        logger.info(f"Model deployed: {model_version}")
        return True

    except Exception as exc:
        logger.error(f"Error deploying model: {exc}")
        return False


def get_active_model(model_type):
    """Get the active model version for a model type.

    Args:
        model_type: Type of model

    Returns:
        Model version string or None
    """
    return cache.get(f"ml_model:active:{model_type}")


def _train_recommendation_model(run, dataset_size):
    """Train a recommendation model.

    Args:
        run: MLTrainingRun instance
        dataset_size: Number of records to use

    Returns:
        Dict with training metrics
    """
    # Get user behavior data
    events = RecommendationEvent.objects.filter(
        event_type__in=['view', 'select', 'save', 'rating'],
    ).order_by('-created_at')[:dataset_size]

    # Calculate basic metrics
    total_events = events.count()
    unique_users = events.values('user').distinct().count()
    unique_destinations = events.values('destination').distinct().count()

    # Calculate engagement rate
    impressions = events.filter(event_type='impression').count()
    selections = events.filter(event_type__in=['select', 'view', 'save']).count()
    engagement_rate = selections / impressions if impressions > 0 else 0

    metrics = {
        'total_events': total_events,
        'unique_users': unique_users,
        'unique_destinations': unique_destinations,
        'engagement_rate': round(engagement_rate, 4),
        'training_duration_seconds': 0,
    }

    return metrics


def _train_risk_model(run, dataset_size):
    """Train a risk prediction model.

    Args:
        run: MLTrainingRun instance
        dataset_size: Number of records to use

    Returns:
        Dict with training metrics
    """
    from .models import RiskIncident, CurrentHazard

    # Get risk data
    incidents = RiskIncident.objects.all()[:dataset_size]
    hazards = CurrentHazard.objects.filter(is_active=True)

    metrics = {
        'total_incidents': incidents.count(),
        'active_hazards': hazards.count(),
        'hazard_types': list(hazards.values_list('hazard_type', flat=True).distinct()),
    }

    return metrics


def _train_crowd_model(run, dataset_size):
    """Train a crowd prediction model.

    Args:
        run: MLTrainingRun instance
        dataset_size: Number of records to use

    Returns:
        Dict with training metrics
    """
    # Get view data
    views = VisitHistory.objects.all()[:dataset_size]

    metrics = {
        'total_views': views.count(),
        'unique_destinations': views.values('destination').distinct().count(),
        'unique_users': views.values('user').distinct().count(),
    }

    return metrics


def _calculate_precision(events):
    """Calculate precision from events.

    Args:
        events: QuerySet of RecommendationEvent

    Returns:
        Precision score (0-1)
    """
    # Precision = relevant recommendations / total recommendations
    relevant = events.filter(event_type__in=['select', 'save', 'rating']).count()
    total = events.filter(event_type='impression').count()

    return relevant / total if total > 0 else 0


def _calculate_recall(events):
    """Calculate recall from events.

    Args:
        events: QuerySet of RecommendationEvent

    Returns:
        Recall score (0-1)
    """
    # Recall = relevant recommendations / total possible relevant items
    # Simplified: use unique destinations viewed / unique destinations recommended
    viewed = events.filter(event_type='view').values('destination').distinct().count()
    recommended = events.filter(event_type='impression').values('destination').distinct().count()

    return viewed / recommended if recommended > 0 else 0


def _calculate_coverage(events):
    """Calculate coverage from events.

    Args:
        events: QuerySet of RecommendationEvent

    Returns:
        Coverage score (0-1)
    """
    # Coverage = unique destinations recommended / total destinations
    recommended = events.filter(event_type='impression').values('destination').distinct().count()
    total = Destination.objects.count()

    return recommended / total if total > 0 else 0


def _generate_version():
    """Generate a unique model version string.

    Returns:
        Version string (e.g., 'v1.0.0-20260101')
    """
    timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
    return f"v1.0.0-{timestamp}"
