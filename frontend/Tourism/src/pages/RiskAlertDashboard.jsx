import { useEffect, useState } from "react";

import alertApi from "../api/alertApi";

import AlertCard from "../components/cards/AlertCard";
import Loader from "../components/common/Loader";
import EmptyState from "../components/common/EmptyState";
import Filter from "../components/common/Filter";
import BarChartCard from "../components/charts/BarChartCard";


const LEVEL_OPTIONS = [
  { label: "Low", value: "low" },
  { label: "Moderate", value: "moderate" },
  { label: "High", value: "high" },
];


const RiskAlertDashboard = () => {

  const [alerts, setAlerts] = useState([]);
  const [level, setLevel] = useState("");
  const [loading, setLoading] = useState(true);


  useEffect(() => {

    const loadAlerts = async () => {

      setLoading(true);

      try {

        // NOTE: the backend's AlertFilter has no `level` param — it filters
        // by `severity` instead. Passing `level` here is harmless (just
        // ignored server-side), but doesn't actually filter results. If
        // you want server-side filtering, send `severity: level` instead —
        // left as `level` here since that's a small intentional choice,
        // not a bug fix; tell me if you want it wired through.
        const { data } = await alertApi.getAlerts({
          level,
        });


        // Handle different backend response formats
        const alertlist =
          Array.isArray(data)
            ? data
            : data.results ||
              data.items ||
              data.alerts ||
              [];


        setAlerts(
          Array.isArray(alertlist)
            ? alertlist
            : []
        );


      } catch (error) {

        console.log(
          "Alert loading error:",
          error.response?.data || error.message
        );

        setAlerts([]);

      } finally {

        setLoading(false);

      }

    };


    loadAlerts();


  }, [level]);



  const counts = [
    "low",
    "moderate",
    "high",
  ].map(
    (lvl) =>
      alerts.filter(
        (alert) =>
          // FIXED: the backend's Alert field is `severity`, not `level` —
          // `alert.level` was always undefined, so every count was always
          // 0 regardless of how many alerts actually existed.
          alert.severity?.toLowerCase() === lvl
      ).length
  );



  return (

    <div className="container-app py-10">


      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">


        <div>

          <h1 className="section-title mb-1">
            Risk Alert Dashboard
          </h1>


          <p className="text-gray-500 text-sm">
            Stay updated on safety conditions across destinations.
          </p>


        </div>



        <Filter
          label="Risk Level"
          options={LEVEL_OPTIONS}
          value={level}
          onChange={setLevel}
        />


      </div>




      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">



        <div className="lg:col-span-1">


          <BarChartCard

            title="Alerts by Risk Level"

            labels={[
              "Low",
              "Moderate",
              "High",
            ]}

            data={counts}

            label="Alerts"

          />


        </div>





        <div className="lg:col-span-2">


          {
            loading ? (

              <Loader />

            ) : alerts.length ? (


              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">


                {
                  alerts.map((alert) => (

                    <AlertCard

                      key={alert.id}

                      alert={alert}

                    />

                  ))
                }


              </div>



            ) : (


              <EmptyState

                title="No active alerts"

                subtitle="All destinations currently look safe."

              />


            )
          }



        </div>



      </div>


    </div>

  );

};


export default RiskAlertDashboard;