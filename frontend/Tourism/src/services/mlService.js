const ML_URL = "http://localhost:8001";


// Recommendation

export async function getRecommendations(interest){

    const response = await fetch(
        `${ML_URL}/recommendation/`,
        {
            method:"POST",

            headers:{
                "Content-Type":"application/json"
            },

            body:JSON.stringify({
                interest:interest
            })
        }
    );


    if(!response.ok){
        throw new Error(
            "Recommendation failed"
        );
    }


    return await response.json();

}



// Risk prediction

export async function getRisk(data){

    const response = await fetch(
        `${ML_URL}/risk/predict`,
        {
            method:"POST",

            headers:{
                "Content-Type":"application/json"
            },

            body:JSON.stringify(data)
        }
    );


    if(!response.ok){
        throw new Error(
            "Risk prediction failed"
        );
    }


    return await response.json();

}



// Emergency nearest facilities

export async function getEmergency(
    lat,
    lon,
    category="hospital"
){

    const response = await fetch(
        `${ML_URL}/emergency/nearest?lat=${lat}&lon=${lon}&category=${category}`
    );


    if(!response.ok){
        throw new Error(
            "Emergency search failed"
        );
    }


    return await response.json();

}



// Budget prediction

export async function predictBudget(data){

    const response = await fetch(
        `${ML_URL}/budget/predict-budget`,
        {
            method:"POST",

            headers:{
                "Content-Type":"application/json"
            },

            body:JSON.stringify(data)
        }
    );


    if(!response.ok){
        throw new Error(
            "Budget prediction failed"
        );
    }


    return await response.json();

}



// Translation

export async function translateText(
    text,
    target_lang="ne"
){

    const response = await fetch(
        `${ML_URL}/translation/translate`,
        {
            method:"POST",

            headers:{
                "Content-Type":"application/json"
            },

            body:JSON.stringify({

                text:text,

                target_lang:target_lang

            })
        }
    );


    if(!response.ok){
        throw new Error(
            "Translation failed"
        );
    }


    return await response.json();

}