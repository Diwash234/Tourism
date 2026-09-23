import { useEffect, useId, useRef } from "react"
import { FiAlertTriangle, FiChevronLeft, FiChevronRight, FiInbox, FiX } from "react-icons/fi"

export function AdminStatusBadge({ value = "unknown" }) {
  const styles = { active:"bg-emerald-500/15 text-emerald-300",approved:"bg-emerald-500/15 text-emerald-300",published:"bg-emerald-500/15 text-emerald-300",sent:"bg-emerald-500/15 text-emerald-300",completed:"bg-emerald-500/15 text-emerald-300",pending:"bg-amber-500/15 text-amber-300",draft:"bg-amber-500/15 text-amber-300",queued:"bg-sky-500/15 text-sky-300",scheduled:"bg-sky-500/15 text-sky-300",inactive:"bg-slate-500/20 text-slate-300",archived:"bg-rose-500/15 text-rose-300",rejected:"bg-rose-500/15 text-rose-300",failed:"bg-rose-500/15 text-rose-300",flagged:"bg-orange-500/15 text-orange-300" }
  return <span className={`inline-flex rounded-full px-2.5 py-1 text-[11px] font-bold capitalize ${styles[value] || "bg-slate-700 text-slate-200"}`}>{String(value).replaceAll("_", " ")}</span>
}

export function AdminPagination({ page, pages, onChange, disabled = false }) {
  if (pages <= 1) return null
  return <nav className="flex justify-end items-center gap-3 text-xs" aria-label="Pagination"><button type="button" disabled={disabled||page<=1} onClick={()=>onChange(page-1)} className="admin-icon-button" aria-label="Previous page"><FiChevronLeft/></button><span aria-live="polite">Page {page} of {pages}</span><button type="button" disabled={disabled||page>=pages} onClick={()=>onChange(page+1)} className="admin-icon-button" aria-label="Next page"><FiChevronRight/></button></nav>
}

export function AdminEmptyState({ title = "No records found", description = "Try changing your filters." }) {
  return <div className="p-10 text-center text-slate-500" role="status"><FiInbox className="mx-auto mb-2" size={28}/><b className="block text-slate-300">{title}</b><p className="text-xs mt-1">{description}</p></div>
}

export function AdminField({ label, hint, error, children }) {
  const id = useId()
  return <label className="block text-xs text-slate-300" htmlFor={id}><span className="font-semibold">{label}</span>{typeof children === "function" ? children({ id, "aria-describedby": hint||error ? `${id}-help` : undefined, "aria-invalid": Boolean(error) }) : children}{(hint||error)&&<span id={`${id}-help`} className={`block mt-1 ${error?"text-rose-300":"text-slate-500"}`}>{error||hint}</span>}</label>
}

export function AdminConfirmDialog({ open, title = "Confirm action", message, confirmLabel = "Confirm", destructive = false, onConfirm, onCancel }) {
  const cancelRef=useRef(null);const titleId=useId();const descriptionId=useId()
  useEffect(()=>{if(!open)return;cancelRef.current?.focus();const key=e=>e.key==="Escape"&&onCancel();document.addEventListener("keydown",key);return()=>document.removeEventListener("keydown",key)},[open,onCancel])
  if(!open)return null
  return <div className="fixed inset-0 z-[100] grid place-items-center bg-black/75 p-4" role="presentation" onMouseDown={e=>e.target===e.currentTarget&&onCancel()}><section role="alertdialog" aria-modal="true" aria-labelledby={titleId} aria-describedby={descriptionId} className="w-full max-w-md rounded-2xl border border-slate-700 bg-slate-950 p-5 text-slate-100 shadow-2xl"><div className="flex justify-between gap-3"><FiAlertTriangle className={destructive?"text-rose-400":"text-amber-400"} size={24}/><button ref={cancelRef} onClick={onCancel} className="admin-icon-button ml-auto" aria-label="Close confirmation"><FiX/></button></div><h2 id={titleId} className="mt-3 text-xl font-black">{title}</h2><p id={descriptionId} className="mt-2 text-sm text-slate-400">{message}</p><div className="mt-5 flex justify-end gap-2"><button ref={cancelRef} onClick={onCancel} className="admin-secondary-button">Cancel</button><button onClick={onConfirm} className={destructive?"admin-danger-button":"admin-primary-button"}>{confirmLabel}</button></div></section></div>
}

export function AdminTableShell({ title, count, toolbar, children, footer }) {
  return <section className="overflow-hidden rounded-2xl border border-slate-700 bg-slate-950/80" aria-label={title}><header className="flex flex-wrap items-center gap-3 border-b border-slate-800 p-4"><div><h2 className="font-black">{title}</h2>{count!=null&&<p className="text-xs text-slate-500">{count.toLocaleString()} records</p>}</div>{toolbar&&<div className="ml-auto flex flex-wrap gap-2">{toolbar}</div>}</header><div className="overflow-x-auto">{children}</div>{footer&&<footer className="border-t border-slate-800 p-3">{footer}</footer>}</section>
}
