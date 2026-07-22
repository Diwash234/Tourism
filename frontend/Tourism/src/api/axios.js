import axios from "axios"


const api = axios.create({

    baseURL: "http://localhost:8000/api/v1",

    headers:{
        "Content-Type":"application/json"
    }

})


// Attach JWT token automatically
api.interceptors.request.use(
    (config)=>{

        const token =
            localStorage.getItem("access")

        if(token){

            config.headers.Authorization =
                `Bearer ${token}`

        }

        return config

    },

    (error)=>Promise.reject(error)

)


// NOTE: this file (axios.js) is a simpler duplicate of axiosClient.js —
// it has no 401/refresh-token handling at all. weatherApi.js and
// recommendationApi.js import THIS file instead of axiosClient.js, so
// they won't auto-refresh an expired token the way everything else does.
// Not broken, just inconsistent — consider switching those two imports to
// axiosClient.js instead, or leave as-is if that's intentional.
export default api