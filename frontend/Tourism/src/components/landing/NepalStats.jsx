import React from "react"
import { FadeIn } from "../common/MotionSystem"

const STATS = [
  { value: "8", label: "HIGHEST MOUNTAINS", sub: "Peaks above 8,000 meters including Mt. Everest" },
  { value: "14", label: "NATIONAL CONSERVATION ZONES", sub: "Protected national parks & wildlife sanctuaries" },
  { value: "77", label: "DISTRICTS", sub: "Spanning across all 7 provinces of Nepal" },
  { value: "100+", label: "RECORDED DESTINATIONS", sub: "Landmark heritage, trekking & cultural circuits" },
]

export default function NepalStats() {
  return (
    <section className="py-16 bg-[#F7F8F5] border-y border-[#E5E0D5]">
      <div className="container-app max-w-6xl mx-auto">
        <div className="text-center max-w-2xl mx-auto mb-12">
          <span className="px-3.5 py-1 rounded-full bg-[#E5E0D5] text-[#102A2E] text-xs font-black uppercase tracking-widest">
            NEPAL, IN NUMBERS
          </span>
          <h2 className="text-3xl sm:text-4xl font-extrabold text-[#172022] mt-2 tracking-tight">
            The Roof of the World
          </h2>
          <p className="text-sm text-[#697675] mt-1">
            Data-driven overview of Nepal's unique geography, elevation zones, and cultural heritage.
          </p>
        </div>

        <div className="grid grid-cols-2 lg:grid-cols-4 gap-6 text-center">
          {STATS.map((stat, idx) => (
            <FadeIn key={stat.label} delay={idx * 0.1} className="p-6 rounded-3xl bg-white border border-[#E5E0D5] shadow-xs flex flex-col justify-between">
              <div>
                <span className="text-4xl sm:text-5xl font-black text-[#102A2E] tracking-tight block">
                  {stat.value}
                </span>
                <span className="text-xs font-black uppercase tracking-wider text-[#D99048] block mt-2">
                  {stat.label}
                </span>
              </div>
              <p className="text-[11px] text-[#697675] mt-3 leading-relaxed border-t border-slate-100 pt-3">
                {stat.sub}
              </p>
            </FadeIn>
          ))}
        </div>
      </div>
    </section>
  )
}
