import { motion } from "framer-motion";

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
    fact: "The cow is Nepal's national animal",
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
    fact: "Symbol of Nepal's unity",
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
    <section className="rounded-2xl overflow-hidden mb-8">

      <div
        className="p-6 md:p-8 text-white"
        style={{
          backgroundImage:
            "linear-gradient(135deg,#0B3D91,#3f66b8,#F59E0B)",
        }}
      >

        <h2 className="text-2xl font-bold mb-2">
          Nepal's National Identity
        </h2>


        <p className="text-white/80 text-sm mb-6">
          Symbols that represent Nepal's culture and heritage.
        </p>


        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">

          {SYMBOLS.map(({image,label,fact},index)=>(

            <motion.div
              key={label}
              initial={{opacity:0,y:10}}
              animate={{opacity:1,y:0}}
              transition={{delay:index*0.05}}
              className="bg-white/10 rounded-xl p-3 text-center"
            >

              <img
                src={image}
                alt={label}
                className="w-20 h-20 rounded-full object-cover mx-auto mb-2 bg-white"
              />


              <h3 className="text-sm font-semibold">
                {label}
              </h3>


              <p className="text-xs text-white/70 mt-1">
                {fact}
              </p>

            </motion.div>

          ))}

        </div>

      </div>


      <div className="bg-blue-900 py-3 overflow-hidden">

        <div className="marquee-track">

          {[...MARQUEE_ITEMS,...MARQUEE_ITEMS].map((item,i)=>(

            <span
              key={i}
              className="text-white px-8 text-sm whitespace-nowrap"
            >
              {item}
            </span>

          ))}

        </div>

      </div>


    </section>
  );
};


export default NationalSymbols;