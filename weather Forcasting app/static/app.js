let weatherData = null;

let temperatureChart = null;

/* =========================
   DOM ELEMENTS
========================= */

const searchForm = document.getElementById("searchForm");

const cityInput = document.getElementById("cityInput");

const errorMessage = document.getElementById("errorMessage");

const loading = document.getElementById("loading");

const dashboard = document.getElementById("weatherDashboard");

const welcome = document.getElementById("welcome");

const refreshBtn = document.getElementById("refreshBtn");

const locationBtn = document.getElementById("locationBtn");

const demoBtn = document.getElementById("demoBtn");

/* =========================
   LOADING
========================= */

function showLoading() {
  loading.classList.add("active");
}

function hideLoading() {
  loading.classList.remove("active");
}

/* =========================
   ERROR
========================= */

function showError(message) {
  errorMessage.textContent = message;
}

function clearError() {
  errorMessage.textContent = "";
}

/* =========================
   SEARCH WEATHER
========================= */

async function searchWeather(city) {
  if (!city || city.trim() === "") {
    showError("Please enter a city name.");

    return;
  }

  clearError();

  showLoading();

  try {
    const response = await fetch("/weather", {
      method: "POST",

      headers: {
        "Content-Type": "application/json",
      },

      body: JSON.stringify({
        city: city.trim(),
      }),
    });

    const data = await response.json();

    if (!data.success) {
      showError(data.error || "Unable to find weather.");

      return;
    }

    weatherData = data;

    renderWeather(data);
  } catch (error) {
    console.error(error);

    showError("Unable to connect to weather server.");
  } finally {
    hideLoading();
  }
}

/* =========================
   RENDER WEATHER
========================= */

function renderWeather(data) {
  dashboard.classList.remove("hidden");

  welcome.classList.add("hidden");

  document.getElementById("cityName").textContent = data.city;

  document.getElementById("countryName").textContent = data.country;

  document.getElementById("temperature").textContent = data.temperature;

  document.getElementById("feelsLike").textContent = data.feels_like;

  document.getElementById("description").textContent = data.description;

  document.getElementById("tempMax").textContent = `${data.temp_max}°`;

  document.getElementById("tempMin").textContent = `${data.temp_min}°`;

  document.getElementById("humidity").textContent = data.humidity;

  document.getElementById("windSpeed").textContent = data.wind_speed;

  document.getElementById("pressure").textContent = data.pressure;

  document.getElementById("visibility").textContent = data.visibility;

  document.getElementById("clouds").textContent = data.clouds;

  document.getElementById("windDirection").textContent = data.wind_direction;

  document.getElementById("sunrise").textContent = data.sunrise;

  document.getElementById("sunset").textContent = data.sunset;

  document.getElementById("latitude").textContent =
    data.coordinates.lat.toFixed(4);

  document.getElementById("longitude").textContent =
    data.coordinates.lon.toFixed(4);

  document.getElementById("updatedTime").textContent =
    new Date().toLocaleTimeString();

  const icon = document.getElementById("weatherIcon");

  icon.src = `https://openweathermap.org/img/wn/${data.icon}@4x.png`;

  renderHourly(data.hourly);

  renderDaily(data.forecast);

  renderChart(data.hourly);

  update3DWeather(data.weather_main);
}

/* =========================
   HOURLY
========================= */

function renderHourly(hourly) {
  const container = document.getElementById("hourlyForecast");

  container.innerHTML = "";

  hourly.forEach((item) => {
    const card = document.createElement("div");

    card.className = "hour-card";

    card.innerHTML = `

            <span class="hour">
                ${item.time}
            </span>

            <img
                src="https://openweathermap.org/img/wn/${item.icon}@2x.png"
                alt="${item.description}"
            >

            <strong>
                ${item.temperature}°
            </strong>

            <small>
                ${item.description}
            </small>

        `;

    container.appendChild(card);
  });
}

/* =========================
   DAILY
========================= */

function renderDaily(days) {
  const container = document.getElementById("dailyForecast");

  container.innerHTML = "";

  days.slice(0, 5).forEach((day) => {
    const card = document.createElement("div");

    card.className = "daily-card";

    card.innerHTML = `

            <div class="date">
                ${day.date}
            </div>

            <img
                src="https://openweathermap.org/img/wn/${day.icon}@2x.png"
                alt="${day.description}"
            >

            <strong>
                ${day.max_temp}°
            </strong>

            <div class="range">
                ${day.min_temp}° / ${day.max_temp}°
            </div>

            <p>
                ${day.description}
            </p>

        `;

    container.appendChild(card);
  });
}

/* =========================
   CHART
========================= */

function renderChart(hourly) {
  const canvas = document.getElementById("temperatureChart");

  if (temperatureChart) {
    temperatureChart.destroy();
  }

  const labels = hourly.map((item) => item.time);

  const temperatures = hourly.map((item) => item.temperature);

  temperatureChart = new Chart(canvas, {
    type: "line",

    data: {
      labels: labels,

      datasets: [
        {
          label: "Temperature °C",

          data: temperatures,

          borderColor: "#22d3ee",

          backgroundColor: "rgba(34,211,238,0.15)",

          fill: true,

          tension: 0.4,

          pointRadius: 4,

          pointHoverRadius: 7,
        },
      ],
    },

    options: {
      responsive: true,

      maintainAspectRatio: false,

      plugins: {
        legend: {
          labels: {
            color: "#ffffff",
          },
        },
      },

      scales: {
        x: {
          ticks: {
            color: "#94a3b8",
          },

          grid: {
            color: "rgba(255,255,255,0.05)",
          },
        },

        y: {
          ticks: {
            color: "#94a3b8",
          },

          grid: {
            color: "rgba(255,255,255,0.05)",
          },
        },
      },
    },
  });
}

/* =========================
   SEARCH EVENT
========================= */

searchForm.addEventListener("submit", (event) => {
  event.preventDefault();

  searchWeather(cityInput.value);
});

/* =========================
   DEMO
========================= */

demoBtn.addEventListener("click", () => {
  cityInput.value = "Pune";

  searchWeather("Pune");
});

/* =========================
   REFRESH
========================= */

refreshBtn.addEventListener("click", () => {
  if (weatherData) {
    searchWeather(weatherData.city);
  }
});

/* =========================
   GEOLOCATION
========================= */

locationBtn.addEventListener("click", () => {
  if (!navigator.geolocation) {
    showError("Geolocation is not supported.");

    return;
  }

  showLoading();

  navigator.geolocation.getCurrentPosition(
    async (position) => {
      try {
        const response = await fetch("/weather/location", {
          method: "POST",

          headers: {
            "Content-Type": "application/json",
          },

          body: JSON.stringify({
            lat: position.coords.latitude,

            lon: position.coords.longitude,
          }),
        });

        const data = await response.json();

        if (!data.success) {
          showError(data.error);

          return;
        }

        weatherData = data;

        renderWeather(data);
      } catch (error) {
        console.error(error);

        showError("Unable to retrieve location weather.");
      } finally {
        hideLoading();
      }
    },

    (error) => {
      hideLoading();

      showError("Location permission was denied or unavailable.");
    },
  );
});

/* ==================================================
   THREE.JS 3D BACKGROUND
================================================== */

let scene;

let camera;

let renderer;

let particles;

let particleGeometry;

let particleMaterial;

let animationId;

function init3D() {
  const canvas = document.getElementById("threeCanvas");

  scene = new THREE.Scene();

  camera = new THREE.PerspectiveCamera(
    75,
    window.innerWidth / window.innerHeight,
    0.1,
    1000,
  );

  camera.position.z = 8;

  renderer = new THREE.WebGLRenderer({
    canvas: canvas,
    alpha: true,
    antialias: true,
  });

  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));

  renderer.setSize(window.innerWidth, window.innerHeight);

  /* PARTICLES */

  particleGeometry = new THREE.BufferGeometry();

  const particleCount = 1800;

  const positions = new Float32Array(particleCount * 3);

  for (let i = 0; i < particleCount * 3; i += 3) {
    positions[i] = (Math.random() - 0.5) * 30;

    positions[i + 1] = (Math.random() - 0.5) * 20;

    positions[i + 2] = (Math.random() - 0.5) * 25;
  }

  particleGeometry.setAttribute(
    "position",
    new THREE.BufferAttribute(positions, 3),
  );

  particleMaterial = new THREE.PointsMaterial({
    size: 0.035,

    transparent: true,

    opacity: 0.75,
  });

  particles = new THREE.Points(particleGeometry, particleMaterial);

  scene.add(particles);

  /* 3D WIREFRAME SPHERES */

  const sphereGeometry = new THREE.SphereGeometry(2.2, 32, 32);

  const sphereMaterial = new THREE.MeshBasicMaterial({
    wireframe: true,

    transparent: true,

    opacity: 0.06,
  });

  const sphere = new THREE.Mesh(sphereGeometry, sphereMaterial);

  sphere.position.set(6, 2, -5);

  scene.add(sphere);

  animate3D();

  window.addEventListener("resize", resize3D);
}

function animate3D() {
  animationId = requestAnimationFrame(animate3D);

  if (particles) {
    particles.rotation.y += 0.0004;

    particles.rotation.x += 0.0001;
  }

  scene.traverse((object) => {
    if (object instanceof THREE.Mesh) {
      object.rotation.x += 0.00015;

      object.rotation.y += 0.00025;
    }
  });

  renderer.render(scene, camera);
}

function resize3D() {
  camera.aspect = window.innerWidth / window.innerHeight;

  camera.updateProjectionMatrix();

  renderer.setSize(window.innerWidth, window.innerHeight);
}

/* =========================
   WEATHER EFFECT
========================= */

function update3DWeather(type) {
  if (!particleMaterial) {
    return;
  }

  if (type === "Rain") {
    particleMaterial.size = 0.025;

    particleMaterial.opacity = 0.85;
  } else if (type === "Clouds") {
    particleMaterial.size = 0.045;

    particleMaterial.opacity = 0.5;
  } else if (type === "Clear") {
    particleMaterial.size = 0.035;

    particleMaterial.opacity = 0.8;
  } else if (type === "Thunderstorm") {
    particleMaterial.size = 0.055;

    particleMaterial.opacity = 0.95;
  }
}

/* =========================
   START 3D
========================= */

init3D();
