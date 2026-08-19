import { useEffect, useState } from "react"
import { FiDatabase, FiExternalLink, FiImage, FiSearch } from "react-icons/fi"
import adminApi from "../../api/adminApi"

const GROUPS = [
  ["Core", [["destinations","Destinations"],["destination_features","Destination Features"],["destination_images","Destination Images"],["destination_translations","Translations"],["categories","Categories"],["languages","Languages"]]],
  ["Hotels & Bookings", [["hotels","Hotels"],["bookings","Bookings"],["hotel_reviews","Hotel Reviews"]]],
  ["Users", [["reviews","Destination Reviews"],["ratings","Ratings"],["favorites","Favorites"],["visit_history","Visit History"],["family_links","Family Links"],["email_tokens","Email Tokens"]]],
  ["Safety & Services", [["alerts","Alerts"],["current_hazards","Current Hazards"],["emergency_contacts","Emergency Contacts"],["osm_services","OSM Essential Services"],["osm_places","OSM Tourism Places"]]],
  ["Finance & Feedback", [["budgets","Budgets"],["feedback","User Feedback"],["feedback_evidence","Feedback Evidence"]]],
  ["Audit", [["audit_logs","Audit Log Entries"],["error_events","Error Events"]]],
]

export default function DataExplorerPanel() {
  const [resource,setResource]=useState("destinations"), [query,setQuery]=useState(""), [data,setData]=useState({results:[],count:0}), [loading,setLoading]=useState(false)
  const load=()=>{setLoading(true);adminApi.exploreData({resource,q:query}).then(({data})=>setData(data)).catch(()=>setData({results:[],count:0})).finally(()=>setLoading(false))}
  useEffect(load,[resource]) // eslint-disable-line react-hooks/exhaustive-deps
  return <div className="grid lg:grid-cols-[270px_1fr] gap-5">
    <aside className="rounded-2xl bg-slate-950 border border-slate-700 p-4 max-h-[75vh] overflow-y-auto">{GROUPS.map(([group,items])=><div key={group} className="mb-4"><h3 className="text-[10px] uppercase tracking-widest text-slate-500 font-black mb-2">{group}</h3>{items.map(([id,label])=><button key={id} onClick={()=>setResource(id)} className={`block w-full text-left px-3 py-2 rounded-lg text-xs mb-1 ${resource===id?'bg-amber-400 text-slate-950 font-black':'text-slate-300 hover:bg-slate-800'}`}>{label}</button>)}</div>)}</aside>
    <section className="rounded-2xl bg-slate-950 border border-slate-700 p-5 overflow-hidden"><div className="flex flex-wrap gap-2 justify-between mb-4"><div><h2 className="text-xl text-white font-black flex items-center gap-2"><FiDatabase/>Database Explorer</h2><p className="text-xs text-slate-400">{data.count} records · searchable read view</p></div><div className="flex"><input value={query} onChange={e=>setQuery(e.target.value)} onKeyDown={e=>e.key==='Enter'&&load()} className="rounded-l-xl bg-slate-800 border border-slate-600 px-3 text-sm text-white" placeholder="Search records…"/><button onClick={load} className="rounded-r-xl bg-amber-400 px-4"><FiSearch/></button></div></div>
      <a href="/django-admin/" target="_blank" rel="noreferrer" className="text-xs text-amber-300 inline-flex items-center gap-1 mb-3">Open full Django add/edit/delete administration <FiExternalLink/></a>
      {resource==="destinations"&&<p className="text-xs text-slate-400 mb-3"><FiImage className="inline"/> Search a destination here, then use Multi-Source Image Pipeline to inspect, upload, browse local files and set covers.</p>}
      <div className="overflow-auto max-h-[62vh]"><table className="min-w-full text-xs"><thead className="sticky top-0 bg-slate-900"><tr>{data.columns?.map(c=><th key={c} className="text-left text-slate-400 px-3 py-2 whitespace-nowrap">{c}</th>)}</tr></thead><tbody>{loading?<tr><td className="text-slate-400 p-5">Loading…</td></tr>:data.results.map((row,i)=><tr key={row.id||i} className="border-t border-slate-800">{data.columns?.map(c=><td key={c} className="text-slate-300 px-3 py-2 max-w-72 truncate">{row[c]===null?'—':String(row[c]??'')}</td>)}</tr>)}</tbody></table></div>
    </section>
  </div>
}
