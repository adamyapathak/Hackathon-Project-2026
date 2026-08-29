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
    let response = await fetch("http://127.0.0.1:8000");
    object_data = await response.json();
    insert_data();
}

function first_load() {
    document.getElementById("intro_stuff").style.display = "none";
    document.getElementById("loading_img").style.display = "inline";
    fetch_clemson_data();
}

function insert_data() {
    document.getElementById("local_time").innerText = "Local Time: " + specific_info.local_time;
    document.getElementById("conditions").innerText = "Sky Conditions " + specific_info.sky_cond;
    document.getElementById("highlights").innerText = specific_info.highlights;
    document.getElementById("gemini").innerText = specific_info.overview;
}

function show_light_pollution() { //show what night sky looks like with light pollution
    document.getElementsByTagName("html")[0].style.backgroundImage = "";
    document.getElementById("light_pollution_txtbox").style.display = "inline";
}

function remove_light_pollution() { //show what night sky should look like without light pollution 
    document.getElementsByTagName("html")[0].style.backgroundImage = "url(https://www.adlerplanetarium.org/wp-content/uploads/bis-images/1074/Merdith-Stepian-Sark-Island-1200x800-f50_50.png)";
    document.getElementById("light_pollution_txtbox").style.display = "none";
}