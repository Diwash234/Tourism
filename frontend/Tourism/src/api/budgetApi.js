import api from "./axios"


const budgetApi={


getSummary(){

return api.get(
"/budget/summary"
)

}


}


export default budgetApi