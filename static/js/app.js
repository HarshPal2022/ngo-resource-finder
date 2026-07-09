const resultsContainer=document.getElementById("resultsContainer");
const loading=document.getElementById("loading");
const emptyState=document.getElementById("emptyState");
const resultCount=document.getElementById("resultCount");
const ngoCount=document.getElementById("ngoCount");

const searchBtn=document.getElementById("searchBtn");
const recommendBtn=document.getElementById("recommendBtn");

const searchInput=document.getElementById("searchInput");
const recommendInput=document.getElementById("recommendInput");

const districtSearch=document.getElementById("districtSearch");
const districtRecommend=document.getElementById("districtRecommend");

const cardTemplate=document.getElementById("ngoCardTemplate");

window.onload=async()=>{

    await loadNGOCount();
    await loadDistricts();

};

async function loadNGOCount(){
    try{

        const response=await fetch("/api/ngos");
        const data=await response.json();
        ngoCount.textContent=data.count;

    }catch(error){

        ngoCount.textContent="0";
    }
}

async function loadDistricts(){
    try{
        const response=await fetch("/api/districts");
        const data=await response.json();

        data.districts.forEach(district=>{

            const option1=document.createElement("option");
            option1.value=district;
            option1.textContent=district;
            districtSearch.appendChild(option1);

            const option2=document.createElement("option");
            option2.value=district;
            option2.textContent=district;
            districtRecommend.appendChild(option2);
        });
    }catch(error){

        console.log(error);
    }
}

function showLoading(){
    loading.classList.remove("hidden");
    emptyState.classList.add("hidden");
    resultsContainer.innerHTML="";
}

function hideLoading(){

    loading.classList.add("hidden");

}

function renderCards(ngos,isRecommendation=false){
    resultsContainer.innerHTML="";
    resultCount.textContent=`${ngos.length} NGOs`;

    if(ngos.length===0){

        emptyState.classList.remove("hidden");
        return;
    }

    emptyState.classList.add("hidden");
    ngos.forEach(ngo=>{
        const card=cardTemplate.content.cloneNode(true);

        card.querySelector(".ngo-name").textContent=ngo.name||"-";
        card.querySelector(".ngo-district").textContent=ngo.district||"-";
        card.querySelector(".ngo-address").textContent=ngo.address||"-";
        card.querySelector(".ngo-purpose").textContent=ngo.purpose||"-";
        card.querySelector(".ngo-contact").textContent=ngo.contact_person||"-";
        card.querySelector(".ngo-phone").textContent=ngo.mobile||ngo.phone||"-";
        card.querySelector(".ngo-email").textContent=ngo.email||"-";

        const website=card.querySelector(".ngo-website");

        if(ngo.website){
            website.href=ngo.website;
            website.textContent=ngo.website;
        }else{
            website.textContent="-";
            website.removeAttribute("href");
        }
        const visit=card.querySelector(".ngo-url");
        visit.href=ngo.url||"#";
        if(isRecommendation && ngo.score!==undefined){
            const badge=card.querySelector(".score");
            badge.classList.remove("hidden");
            badge.textContent=`${(ngo.score*100).toFixed(1)}% Match`;
        }
        resultsContainer.appendChild(card);
    });
}

searchBtn.addEventListener("click",async()=>{
    const keyword=searchInput.value.trim();
    const district=districtSearch.value;

    showLoading();
    try{
        const params=new URLSearchParams();
        if(keyword!=="")
            params.append("q",keyword);
        if(district!=="")
            params.append("district",district);
        const response=await fetch(`/api/search?${params.toString()}`);
        const data=await response.json();
        hideLoading();
        renderCards(data.results,false);
    }catch(error){
        hideLoading();
        alert("Search failed.");
    }
});

recommendBtn.addEventListener("click",async()=>{
    const query=recommendInput.value.trim();
    const district=districtRecommend.value;

    if(query===""){
        alert("Please enter your requirement.");
        return;
    }
    showLoading();

    try{
        const response=await fetch("/api/recommend",{
            method:"POST",
            headers:{
                "Content-Type":"application/json"
            },

            body:JSON.stringify({
                query:query,
                district:district
            })
        });

        const data=await response.json();
        hideLoading();
        renderCards(data.results,true);

    }catch(error){
        hideLoading();
        alert("Recommendation failed.");

    }
});