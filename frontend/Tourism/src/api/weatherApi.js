import api from "./axios"


const weatherApi={


getCurrentWeather(params){

return api.get(
"/weather/current",
{
params
}
)

}


}


export default weatherApi