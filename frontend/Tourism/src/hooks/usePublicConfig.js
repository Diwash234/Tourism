import { useEffect, useState } from "react"
import configApi from "../api/configApi"
let cache=null,pending=null,listeners=new Set()
const load=()=>{if(cache)return Promise.resolve(cache);if(!pending)pending=configApi.getPublicConfig().then(({data})=>{cache=data;listeners.forEach(fn=>fn(data));return data}).catch(()=>({settings:{},pages:[],navigation:[]}));return pending}
export default function usePublicConfig(){const[data,setData]=useState(cache||{settings:{},pages:[],navigation:[]});useEffect(()=>{listeners.add(setData);load().then(setData);return()=>listeners.delete(setData)},[]);const section=(page,key)=>data.pages?.find(p=>p.key===page)?.sections?.find(s=>s.key===key);return{...data,branding:data.settings?.branding||{},section}}
