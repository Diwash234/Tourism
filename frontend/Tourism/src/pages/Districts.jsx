import { useEffect, useMemo, useState } from "react";
import CMSPageIntro from "../components/cms/CMSPageIntro"
import { Link } from "react-router-dom";
import PageHeader from "../components/common/PageHeader";
import districtApi from "../api/districtApi";
import { FiMap } from "react-icons/fi";

/*
 * All 77 districts of Nepal, served by the districts API (§5/§18).
 * Destination counts come from recorded, published destinations —
 * districts without verified data still appear, with count 0, and their
 * detail page labels gaps as "Information unavailable".
 */
export default function Districts() {
  const [rows, setRows] = useState([]);
  const [provinces, setProvinces] = useState([]);
  const [query, setQuery] = useState("");
  const [province, setProvince] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    const timer = setTimeout(() => {
      districtApi
        .districts(province ? { province } : {})
        .then(({ data }) => !cancelled && setRows(data.results || []))
        .catch(() => !cancelled && setError("Districts could not be loaded right now."));
      districtApi
        .provinces()
        .then(({ data }) => !cancelled && setProvinces(data.results || []))
        .catch(() => {});
    }, 0);
    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
  }, [province]);

  const visible = useMemo(() => {
    const q = query.trim().toLowerCase();
    return q ? rows.filter((row) => row.name.toLowerCase().includes(q)) : rows;
  }, [rows, query]);

  return (
    <div className="min-h-screen bg-[#F7F8F5] dark:bg-nav-dark pb-16">
      <CMSPageIntro pageKey="districts" />
      <PageHeader
        title="Districts of Nepal"
        subtitle="All 77 districts with recorded tourism profiles"
        icon={FiMap}
      />
      <div className="container-app mt-6 space-y-6">
        <div className="flex flex-wrap gap-2">
          <label className="relative flex-1 min-w-[14rem]">
            <span className="sr-only">Search districts</span>
            <input
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Search district — e.g. Rolpa"
              className="w-full rounded-xl border border-gray-200 bg-white px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-400"
            />
          </label>
          <select
            value={province}
            onChange={(event) => setProvince(event.target.value)}
            className="rounded-xl border border-gray-200 bg-white px-3 py-2.5 text-sm"
            aria-label="Filter by province"
          >
            <option value="">All provinces</option>
            {provinces.map((item) => (
              <option key={item.slug} value={item.name}>
                {item.name} ({item.district_count})
              </option>
            ))}
          </select>
        </div>

        {error && (
          <p className="text-sm font-bold text-rose-600">{error}</p>
        )}

        {provinces.length > 0 && !query && !province && (
          <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-2">
            {provinces.map((item) => (
              <button
                key={item.slug}
                type="button"
                onClick={() => setProvince(item.name)}
                className="rounded-xl border border-gray-200 bg-white p-3 text-left hover:border-emerald-400 transition-colors"
              >
                <p className="text-xs font-black text-gray-900">{item.name}</p>
                <p className="text-[10px] text-gray-500 mt-0.5">{item.district_count} districts</p>
              </button>
            ))}
          </div>
        )}

        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
          {visible.map((row) => (
            <Link
              key={row.slug}
              to={`/districts/${row.slug}`}
              className="group rounded-2xl border border-gray-200 bg-white p-4 hover:border-emerald-400 hover:shadow-md transition-all"
            >
              <p className="font-black text-sm text-gray-900 group-hover:text-emerald-700">{row.name}</p>
              <p className="text-[11px] text-gray-500 mt-1">
                {row.province} · {row.destination_count > 0 ? `${row.destination_count} recorded places` : "Profile awaiting verified data"}
              </p>
              {row.elevation_m != null && (
                <p className="text-[10px] text-gray-400 mt-0.5">⛰️ ~{row.elevation_m} m</p>
              )}
            </Link>
          ))}
        </div>
        {!error && visible.length === 0 && (
          <p className="text-sm text-gray-500">No district matches “{query}”.</p>
        )}
      </div>
    </div>
  );
}
