let object_data; //for storing data from python backend
let specific_info = {local_time: "", sky_cond: "", highlights: "", overview: ""};

//event listeners for buttons
if(document.getElementById("Start")) {
    document.getElementById("Start").addEventListener("click", first_load);
}

if(document.getElementById("light_pollution_true")) {
    document.getElementById("light_pollution_true").addEventListener("click", show_light_pollution);
}

if(document.getElementById("light_pollution_false")) {
    document.getElementById("light_pollution_false").addEventListener("click", remove_light_pollution);
}

//functions
async function fetch_clemson_data() { //fetch data from python backend + convert to json
    let response = await fetch("http://localhost:3000/");
    object_data = await response.json();
    insert_data();
}

function first_load() {
    document.getElementById("intro_stuff").style.display = "none";
    document.getElementById("loading_img").style.display = "inline";
    fetch_clemson_data();
}

function insert_data() {
    document.getElementById("").innerText = specific_info.local_time;
    document.getElementById("").innerText = specific_info.sky_cond;
    document.getElementById("").innerText = specific_info.highlights;
    document.getElementById("").innerText = specific_info.overview;
}

function show_light_pollution() { //show what night sky looks like with light pollution
    document.getElementsByTagName("html")[0].style.backgroundImage = "";
    document.getElementById("light_pollution_txtbox").style.display = "inline";
}

function remove_light_pollution() { //show what night sky should look like without light pollution 
    document.getElementsByTagName("html")[0].style.backgroundImage = "";
    document.getElementById("light_pollution_txtbox").style.display = "none";
}