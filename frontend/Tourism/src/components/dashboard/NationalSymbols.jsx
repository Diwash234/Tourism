import { motion } from "framer-motion";
import { Link } from "react-router-dom";
import { FiBookOpen } from "react-icons/fi";

import FlagImg from "./flag,png.jfif";
import MapImg from "./map.jfif";
import CowImg from "./cow.jfif";
import DanpheImg from "./images.jfif";
import RhododendronImg from "./rhododendron.jfif";
import EmblemImg from "./emblem.jfif";
import TopiImg from "./dhaka-topi.jfif";
import StupaImg from "./stupa.jfif";

// Export images so other components can use them
export {
  FlagImg,
  MapImg,
  CowImg,
  DanpheImg,
  RhododendronImg,
  EmblemImg,
  TopiImg,
  StupaImg,
};

const SYMBOLS = [
  {
    image: FlagImg,
    label: "National Flag",
    fact: "The only non-rectangular national flag in the world",
  },
  {
    image: MapImg,
    label: "Nepal Map",
    fact: "7 provinces from Terai to the Himalayas",
  },
  {
    image: CowImg,
    label: "National Animal",
    fact: "The cow is Nepal's sacred national animal",
  },
  {
    image: DanpheImg,
    label: "National Bird",
    fact: "Danphe (Himalayan Monal)",
  },
  {
    image: RhododendronImg,
    label: "National Flower",
    fact: "Lali Gurans — Nepal's national flower",
  },
  {
    image: EmblemImg,
    label: "National Emblem",
    fact: "Symbol of Nepal's unity & Everest",
  },
  {
    image: TopiImg,
    label: "Dhaka Topi",
    fact: "Traditional Nepali cap",
  },
  {
    image: StupaImg,
    label: "Stupa",
    fact: "Buddhist heritage monuments",
  },
];

const MARQUEE_ITEMS = [
  "🏔️ Home to 8 of the world's 14 highest peaks",
  "🛕 UNESCO World Heritage Sites",
  "🐅 Chitwan wildlife and Bengal tigers",
  "🪂 Pokhara paragliding destination",
  "🎉 120+ ethnic groups and cultures",
  "🍚 Dal Bhat Power, 24 Hour",
];

const NationalSymbols = () => {
  return (
    <section className="rounded-3xl overflow-hidden mb-8 shadow-xl border border-blue-900/40">
      <div
        className="p-6 md:p-8 text-white space-y-6"
        style={{
          backgroundImage:
            "linear-gradient(135deg,#0B3D91,#2b519e,#F59E0B)",
        }}
      >
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <span className="px-3 py-1 rounded-full bg-amber-400 text-slate-950 text-xs font-black uppercase tracking-wider shadow">
              Discover Nepal — Beyond Everest
            </span>
            <h2 className="text-2xl md:text-3xl font-extrabold text-white mt-1.5">
              Nepal's National Identity & Cultural Symbols
            </h2>
            <p className="text-white/80 text-xs sm:text-sm mt-0.5">
              Official emblems, natural heritage, sacred animals, and national symbols.
            </p>
          </div>

          <Link
            to="/discover-nepal"
            className="px-5 py-2.5 rounded-2xl bg-white hover:bg-amber-400 text-slate-950 font-black text-xs sm:text-sm shadow-lg transition-all hover:scale-105 flex items-center gap-2 shrink-0"
          >
            <FiBookOpen size={16} /> All 26 National Symbols & Heritage Details ➔
          </Link>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          {SYMBOLS.map(({ image, label, fact }, index) => (
            <motion.div
              key={label}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.04 }}
              className="bg-white/10 backdrop-blur rounded-2xl p-3.5 text-center border border-white/15"
            >
              <img
                src={image}
                alt={label}
                className="w-20 h-20 rounded-full object-cover mx-auto mb-2 bg-white shadow-md border-2 border-white/40"
              />
              <h3 className="text-sm font-extrabold text-white">{label}</h3>
              <p className="text-xs text-white/80 mt-0.5 leading-snug">{fact}</p>
            </motion.div>
          ))}
        </div>
      </div>

      <div className="bg-blue-950 py-3 overflow-hidden border-t border-blue-900/60">
        <div className="marquee-track">
          {[...MARQUEE_ITEMS, ...MARQUEE_ITEMS].map((item, i) => (
            <span key={i} className="text-amber-300 font-bold px-8 text-xs whitespace-nowrap">
              {item}
            </span>
          ))}
        </div>
      </div>
    </section>
  );
};

export default NationalSymbols;
