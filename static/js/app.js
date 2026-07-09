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

const pagination=document.getElementById("pagination");
const pageNumbers=document.getElementById("pageNumbers");
const prevPage=document.getElementById("prevPage");
const nextPage=document.getElementById("nextPage");

let currentPage=1;
let totalPages=1;

let currentKeyword="";
let currentDistrict="";

window.onload=async()=>{

    await loadNGOCount();
    await loadDistricts();
    await searchNGOs(1);

};

async function loadNGOCount(){

    try{

        const response=await fetch("/api/ngos");
        const data=await response.json();

        ngoCount.textContent=data.total;

    }catch(error){

        ngoCount.textContent="0";

    }

}

async function loadDistricts(){

    try{

        const response=await fetch("/api/districts");
        const data=await response.json();

        data.districts.forEach(district=>{

            const a=document.createElement("option");
            a.value=district;
            a.textContent=district;
            districtSearch.appendChild(a);

            const b=document.createElement("option");
            b.value=district;
            b.textContent=district;
            districtRecommend.appendChild(b);

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

function renderCards(ngos,recommend=false){

    resultsContainer.innerHTML="";

    resultCount.textContent=`${ngos.length} NGOs`;

    if(ngos.length===0){

        emptyState.classList.remove("hidden");
        pagination.classList.add("hidden");
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

        }

        const visit=card.querySelector(".ngo-url");
        visit.href=ngo.url||"#";

        if(recommend && ngo.score){

            const badge=card.querySelector(".score");

            badge.classList.remove("hidden");
            badge.textContent=`${(ngo.score*100).toFixed(1)}% Match`;

        }

        resultsContainer.appendChild(card);

    });

}

function renderPagination(){

    if(totalPages<=1){

        pagination.classList.add("hidden");
        return;

    }

    pagination.classList.remove("hidden");

    pageNumbers.innerHTML="";

    prevPage.disabled=currentPage===1;
    nextPage.disabled=currentPage===totalPages;

    let start=Math.max(1,currentPage-2);
    let end=Math.min(totalPages,currentPage+2);

    for(let i=start;i<=end;i++){

        const btn=document.createElement("button");

        btn.textContent=i;

        btn.className="px-4 py-2 rounded-lg border";

        if(i===currentPage){

            btn.classList.add("bg-blue-600","text-white");

        }else{

            btn.classList.add("bg-white");

        }

        btn.onclick=()=>searchNGOs(i);

        pageNumbers.appendChild(btn);

    }

}

async function searchNGOs(page=1){

    currentPage=page;

    showLoading();

    try{

        const params=new URLSearchParams();

        if(currentKeyword!=="")
            params.append("q",currentKeyword);

        if(currentDistrict!=="")
            params.append("district",currentDistrict);

        params.append("page",page);

        const response=await fetch(`/api/search?${params.toString()}`);

        const data=await response.json();

        hideLoading();

        totalPages=data.total_pages;

        renderCards(data.results,false);

        renderPagination();

    }catch(error){

        hideLoading();
        alert("Search failed.");

    }

}

searchBtn.addEventListener("click",()=>{

    currentKeyword=searchInput.value.trim();
    currentDistrict=districtSearch.value;

    searchNGOs(1);

});

recommendBtn.addEventListener("click",async()=>{

    const query=recommendInput.value.trim();
    const district=districtRecommend.value;

    if(query===""){

        alert("Enter your requirement.");

        return;
    }
    showLoading();
    pagination.classList.add("hidden");

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

prevPage.onclick=()=>{
    if(currentPage>1){

        searchNGOs(currentPage-1);
    }
};

nextPage.onclick=()=>{
    if(currentPage<totalPages){

        searchNGOs(currentPage+1);
    }
};