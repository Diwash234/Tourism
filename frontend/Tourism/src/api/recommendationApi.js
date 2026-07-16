import api from "./axios"


const recommendationApi = {


getPersonalized(){

return api.get(
"/recommendations/personalized"
)

}


}


export default recommendationApi