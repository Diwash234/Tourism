import { useEffect, useState } from "react"

import RecommendationCard from "../components/cards/RecommendationCard"
import Loader from "../components/common/Loader"
import EmptyState from "../components/common/EmptyState"
import Filter from "../components/common/Filter"

import { getRecommendations } from "../services/mlService"



const CATEGORY_OPTIONS = [
  { label:"Adventure", value:"adventure" },
  { label:"Cultural", value:"cultural" },
  { label:"Nature", value:"nature" },
  { label:"Relaxation", value:"relaxation" },
]



const Recommendation = () => {


  const [items,setItems] = useState([])

  const [category,setCategory] = useState("")

  const [loading,setLoading] = useState(false)




  async function loadRecommendations(){


    try{


      setLoading(true)


      let interest =
      category || "mountain trekking adventure"



      const response =
      await getRecommendations(
        interest
      )



      setItems(
        response.recommendations ||
        response.results ||
        []
      )


    }

    catch(error){

      console.log(
        error
      )

      setItems([])

    }

    finally{

      setLoading(false)

    }


  }





  useEffect(()=>{


    loadRecommendations()


  },[category])






  return (

    <div className="container-app py-10">


      <div className="flex flex-col sm:flex-row justify-between mb-8">


        <div>

          <h1 className="section-title">
            Recommended For You
          </h1>


          <p className="text-gray-500 text-sm">
            AI based destination recommendations.
          </p>

        </div>



        <Filter

          label="Category"

          options={CATEGORY_OPTIONS}

          value={category}

          onChange={setCategory}

        />


      </div>





      {
        loading ?

        <Loader />


        :

        items.length ?


        <div className="grid md:grid-cols-2 gap-6">


        {
          items.map(
            (item,index)=>(

              <RecommendationCard

                key={index}

                item={item}

              />

            )
          )
        }


        </div>


        :


        <EmptyState

          title="No recommendations found"

          subtitle="Try another category."

        />

      }



    </div>

  )

}


export default Recommendation