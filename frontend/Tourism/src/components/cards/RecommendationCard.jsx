// import { Link } from "react-router-dom";
// import { FiTrendingUp, FiMapPin, FiStar } from "react-icons/fi";


// const RecommendationCard = ({ item }) => {


//   const matchScore = Math.round(
//     (item.score || 0) * 100
//   );


//   return (

//     <div
//       className="
//       card-base
//       overflow-hidden
//       flex
//       flex-col
//       sm:flex-row
//       bg-white
//       rounded-xl
//       shadow-sm
//       hover:shadow-lg
//       transition
//       "
//     >


//       {/* Destination Image */}

//       <img
//         src={
//           item.image ||
//           "https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?w=600"
//         }
//         alt={item.name}
//         className="
//         sm:w-44
//         h-44
//         object-cover
//         "
//       />



//       {/* Content */}

//       <div
//         className="
//         p-5
//         flex-1
//         flex
//         flex-col
//         justify-between
//         "
//       >


//         <div>


//           {/* Match Score */}

//           <div
//             className="
//             flex
//             items-center
//             gap-2
//             text-xs
//             font-semibold
//             text-secondary-500
//             mb-2
//             "
//           >

//             <FiTrendingUp size={15}/>

//             {matchScore}% match

//           </div>



//           {/* Name */}

//           <h3
//             className="
//             text-lg
//             font-bold
//             text-dark
//             "
//           >

//             {item.name || "Unknown Destination"}

//           </h3>



//           {/* Category */}

//           <p
//             className="
//             text-sm
//             text-gray-500
//             mt-1
//             "
//           >

//             {item.type}

//             {" • "}

//             {item.category}

//           </p>




//           {/* Location */}

//           <p
//             className="
//             flex
//             items-center
//             gap-1
//             text-sm
//             text-gray-500
//             mt-2
//             "
//           >

//             <FiMapPin size={14}/>


//             {item.city || "Nepal"}

//           </p>



//           {/* Score */}

//           <div
//             className="
//             flex
//             items-center
//             gap-1
//             text-yellow-500
//             text-sm
//             mt-3
//             "
//           >

//             <FiStar
//               className="fill-yellow-400"
//             />


//             AI Score:

//             {
//               item.score
//                 ? item.score.toFixed(2)
//                 : "0"
//             }


//           </div>


//         </div>





//         {/* Button */}

//         <Link

//           to={
//             item.id
//               ? `/destinations/${item.id}`
//               : "#"
//           }

//           className="
//           mt-4
//           inline-block
//           text-sm
//           font-semibold
//           text-primary-500
//           hover:underline
//           "

//         >

//           Explore Destination

//         </Link>


//       </div>


//     </div>

//   );

// };


// export default RecommendationCard;
import { Link } from "react-router-dom"
import { FiTrendingUp } from "react-icons/fi"



const RecommendationCard = ({item}) => {


return (

<div className="card-base p-5">


<div className="flex items-center gap-2 text-green-600 text-sm">

<FiTrendingUp />

{
Math.round(item.score * 100)
}%

match

</div>



<h3 className="font-bold text-lg mt-3">

{item.name}

</h3>



<p className="text-gray-500">

{item.category}

</p>



<p className="text-sm">

📍 {item.city}

</p>



<Link

to={`/destinations/${item.name}`}

className="text-primary-500 mt-3 block"

>

Explore

</Link>


</div>

)


}


export default RecommendationCard