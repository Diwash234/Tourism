import { useEffect, useState } from "react"
import { useSearchParams, Link } from "react-router-dom"

import destinationApi from "../../api/destinationApi"
import userApi from "../../api/userApi"

import DestinationCard from "../../components/cards/DestinationCard"
import SearchBar from "../../components/common/SearchBar"
import Filter from "../../components/common/Filter"
import Pagination from "../../components/common/Pagination"
import Loader from "../../components/common/Loader"
import EmptyState from "../../components/common/EmptyState"

import useGeolocation from "../../hooks/useGeolocation"
import useAuth from "../../hooks/useAuth"
import useToast from "../../hooks/useToast"


/*
 Categories must match DestinationCard themes
*/

const CATEGORY_OPTIONS = [

  {
    label: "Mountains",
    value: "mountains"
  },

  {
    label: "Lakes",
    value: "lakes"
  },

  {
    label: "Forest & Wildlife",
    value: "wildlife"
  },

  {
    label: "Hotels",
    value: "hotels"
  },

  {
    label: "Heritage",
    value: "heritage"
  },

  {
    label: "Adventure",
    value: "adventure"
  }

]


const PAGE_SIZE = 9



const DestinationList = () => {


  const {
    isAuthenticated
  } = useAuth()


  const {
    showToast
  } = useToast()



  const [
    searchParams
  ] = useSearchParams()



  const initialQuery =
    searchParams.get("q") || ""



  const [
    destinations,
    setDestinations
  ] = useState([])



  const [
    totalPages,
    setTotalPages
  ] = useState(1)



  const [
    page,
    setPage
  ] = useState(1)



  const [
    category,
    setCategory
  ] = useState("")



  const [
    query,
    setQuery
  ] = useState(initialQuery)



  const [
    favoriteMap,
    setFavoriteMap
  ] = useState({})



  const [
    loading,
    setLoading
  ] = useState(true)



  const {
    position
  } = useGeolocation()



  const favoriteIds =
    Object.keys(favoriteMap)
    .map(Number)





  /*
  Fetch destinations
  */

  useEffect(() => {


    setLoading(true)



    const params = {

      page,

      limit: PAGE_SIZE

    }



    if(category){

      params.category = category

    }



    if(query){

      params.search = query

      params.q = query

    }



    if(position){

      params.latitude =
      position.lat


      params.longitude =
      position.lng

    }





    destinationApi
    .getAll(params)

    .then(({data})=>{


      const results =
      data.results || data || []



      setDestinations(results)



      setTotalPages(

        data.total_pages ||
        data.totalPages ||
        1

      )


    })


    .catch(()=>{


      setDestinations([])


    })


    .finally(()=>{


      setLoading(false)


    })



  },[
    page,
    category,
    query,
    position
  ])








  /*
  Load favorites
  */


  useEffect(()=>{


    if(!isAuthenticated){

      setFavoriteMap({})

      return

    }



    userApi
    .getFavorites()


    .then(({data})=>{


      const list =
      data.results ||
      data ||
      []



      const map = {}



      list.forEach((favorite)=>{


        map[favorite.destination] =
        favorite.id


      })



      setFavoriteMap(map)



    })


    .catch(()=>{


      setFavoriteMap({})


    })



  },[
    isAuthenticated
  ])








  /*
  Favorite toggle
  */


  const handleToggleFavorite =
  async(id)=>{


    if(!isAuthenticated){

      showToast(
        "Please login to save favorites",
        "info"
      )

      return

    }



    try{


      if(
        favoriteMap[id]
      ){


        await userApi.removeFavorite(
          favoriteMap[id]
        )



        setFavoriteMap(prev=>{


          const updated =
          {
            ...prev
          }



          delete updated[id]



          return updated


        })



      }


      else{


        const {
          data
        } =
        await userApi.addFavorite(id)



        setFavoriteMap(prev=>({

          ...prev,

          [id]:
          data.id

        }))


      }


    }


    catch{


      showToast(
        "Could not update favorites",
        "error"
      )


    }



  }








  return (

    <div className="
    container-app
    py-10
    fade-in
    ">



      <div className="
      flex
      items-center
      justify-between
      flex-wrap
      gap-3
      ">


        <h1 className="
        section-title
        ">

          Explore Destinations

        </h1>



        <Link

        to="/destinations/submit"

        className="
        btn-outline
        text-sm
        "

        >

          + Suggest a Place


        </Link>



      </div>






      <div className="
      flex
      flex-col
      sm:flex-row
      gap-4
      mb-8
      ">


        <SearchBar


        className="
        flex-1
        "


        defaultValue={
          initialQuery
        }


        onSearch={(value)=>{


          setQuery(value)

          setPage(1)


        }}


        />





        <Filter


        label=""


        options={
          CATEGORY_OPTIONS
        }


        value={
          category
        }


        onChange={(value)=>{


          setCategory(value)

          setPage(1)


        }}


        />


      </div>







      {
      loading ?


      (

        <Loader/>

      )


      :


      destinations.length ?


      (

        <>


        <div className="
        grid
        grid-cols-1
        sm:grid-cols-2
        lg:grid-cols-3
        gap-6
        ">


        {
        destinations.map(
        (destination)=>(


          <DestinationCard


          key={
            destination.id
          }


          destination={
            destination
          }


          isFavorite={
            favoriteIds.includes(
              destination.id
            )
          }


          onToggleFavorite={
            handleToggleFavorite
          }


          />


        ))
        }


        </div>





        <Pagination


        currentPage={
          page
        }


        totalPages={
          totalPages
        }


        onPageChange={
          setPage
        }


        />



        </>


      )


      :


      (

        <EmptyState


        title="
        No destinations found
        "


        subtitle="
        Try adjusting your search or filters.
        "


        />


      )

      }



    </div>

  )

}


export default DestinationList