import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import PageHeader from "../components/common/PageHeader";
import districtApi from "../api/districtApi";
import { FiMap } from "react-icons/fi";

/*
 * One district's tourism profile (§18). Everything renders from the
 * districts API: recorded destinations grouped by category, hospitals,
 * police stations, nearest districts. Unverified fields are explicitly
 * "Information unavailable" — never invented.
 */
export default function DistrictDetail() {
  const { slug } = useParams();
  const [data, setData] = useState(null);
  const [state, setState] = useState("loading");

  useEffect(() => {
    let cancelled = false;
    const timer = setTimeout(() => {
      setState("loading");
      districtApi
        .district(slug)
        .then(({ data: payload }) => {
          if (cancelled) return;
          setData(payload);
          setState("ready");
        })
        .catch(() => !cancelled && setState("missing"));
    }, 0);
    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
  }, [slug]);

  if (state === "loading") {
    return <div className="container-app py-20 text-center text-sm text-gray-500">Loading district profile…</div>;
  }
  if (state === "missing" || !data) {
    return (
      <div className="container-app py-20 text-center space-y-3">
        <p className="text-sm font-bold text-gray-700">This district has no profile yet.</p>
        <Link to="/districts" className="text-sm font-bold text-emerald-600 hover:underline">
          Browse all 77 districts →
        </Link>
      </div>
    );
  }

  const categories = Object.entries(data.destinations_by_category || {});

  return (
    <div className="min-h-screen bg-[#F7F8F5] dark:bg-nav-dark pb-16">
      <PageHeader
        title={data.name}
        subtitle={`${data.province} Province${data.elevation_m != null ? ` · ~${data.elevation_m} m` : ""}`}
        icon={FiMap}
      />

      <div className="container-app mt-6 space-y-6">
        {data.data_note && (
          <p className="rounded-2xl border border-amber-300 bg-amber-50 p-4 text-sm text-amber-800">
            {data.data_note}
          </p>
        )}

        <div className="flex flex-wrap gap-2 text-xs">
          <Link to={`/itinerary`} className="rounded-xl bg-emerald-600 px-4 py-2 font-bold text-white hover:bg-emerald-500">
            Plan a trip to {data.name} →
          </Link>
          <Link to={`/navigation?dest=${encodeURIComponent(data.name)}`} className="rounded-xl border border-emerald-600 px-4 py-2 font-bold text-emerald-700 hover:bg-emerald-50">
            Navigate here
          </Link>
          <Link to="/districts" className="rounded-xl border border-gray-300 px-4 py-2 font-bold text-gray-600 hover:bg-gray-100">
            All districts
          </Link>
        </div>

        <section className="rounded-2xl border border-gray-200 bg-white p-5">
          <h2 className="text-sm font-black uppercase tracking-wider text-emerald-700 mb-2">About {data.name}</h2>
          {data.description === "Information unavailable" && data.summary ? (
            <>
              <p className="text-sm text-gray-700">{data.summary}</p>
              <p className="text-[10px] font-black uppercase tracking-wider text-gray-400 mt-2">
                Auto-generated administrative summary · curated description pending
              </p>
            </>
          ) : (
            <p className="text-sm text-gray-700">{data.description}</p>
          )}
          <p className="text-xs text-gray-500 mt-2">
            Region: {data.region_type} · Province: {data.province}
          </p>
        </section>

        {categories.length > 0 && (
          <section className="space-y-4">
            <h2 className="text-sm font-black uppercase tracking-wider text-emerald-700">
              Recorded places ({data.destination_count})
            </h2>
            <div className="grid md:grid-cols-2 gap-4">
              {categories.map(([category, places]) => (
                <div key={category} className="rounded-2xl border border-gray-200 bg-white p-4">
                  <h3 className="text-xs font-black text-gray-900 mb-2">{category}</h3>
                  <ul className="space-y-1.5">
                    {places.map((place) => (
                      <li key={place.slug} className="flex items-center justify-between gap-2 text-sm">
                        <Link to={`/destinations/${place.slug}`} className="font-semibold text-emerald-700 hover:underline truncate">
                          {place.name}
                        </Link>
                        {place.rating != null && <span className="text-amber-500 text-xs font-bold whitespace-nowrap">★ {place.rating.toFixed(1)}</span>}
                      </li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>
          </section>
        )}

        <div className="grid md:grid-cols-2 gap-4">
          <section className="rounded-2xl border border-gray-200 bg-white p-4">
            <h3 className="text-xs font-black text-gray-900 mb-2">🏥 Hospitals & health</h3>
            {data.hospitals?.length ? (
              <ul className="space-y-1.5 text-sm text-gray-700">
                {data.hospitals.map((hospital) => (
                  <li key={hospital.name}>
                    <b>{hospital.name}</b> · {hospital.phone}
                    <span className="block text-[11px] text-gray-500">{hospital.address} (at {hospital.destination})</span>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-xs text-gray-500">Information unavailable</p>
            )}
          </section>
          <section className="rounded-2xl border border-gray-200 bg-white p-4">
            <h3 className="text-xs font-black text-gray-900 mb-2">🚓 Safety & emergency</h3>
            {data.police_stations?.length ? (
              <ul className="space-y-1.5 text-sm text-gray-700">
                {data.police_stations.map((station) => (
                  <li key={station.name}>
                    <b>{station.name}</b> · {station.phone}
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-xs text-gray-500">Information unavailable</p>
            )}
            <p className="text-xs text-gray-600 mt-3">
              National: Police <a className="font-bold text-emerald-700" href="tel:100">100</a> · Ambulance{" "}
              <a className="font-bold text-emerald-700" href="tel:102">102</a> · Fire{" "}
              <a className="font-bold text-emerald-700" href="tel:101">101</a>
            </p>
          </section>
        </div>

        {data.nearby_districts?.length > 0 && (
          <section className="rounded-2xl border border-gray-200 bg-white p-4">
            <h3 className="text-xs font-black text-gray-900 mb-2">Nearby districts</h3>
            <div className="flex flex-wrap gap-2">
              {data.nearby_districts.map((near) => (
                <Link
                  key={near.slug}
                  to={`/districts/${near.slug}`}
                  className="rounded-xl border border-gray-200 px-3 py-1.5 text-xs font-bold text-gray-700 hover:border-emerald-400 hover:text-emerald-700"
                >
                  {near.name} · {near.distance_km} km
                </Link>
              ))}
            </div>
          </section>
        )}
      </div>
    </div>
  );
}
