document.addEventListener("DOMContentLoaded", () => {
  // Create the page transition overlay
  const overlay = document.createElement("div")
  overlay.className = "page-transition-overlay"

  // Create the top progress bar
  const topProgress = document.createElement("div")
  topProgress.className = "page-transition-top-progress"

  // Create the content for the overlay
  overlay.innerHTML = `
    <div class="page-transition-content">
      <div class="page-transition-spinner">
        <div class="page-transition-icon">🔄</div>
      </div>
      <h3 class="page-transition-title">Loading Page</h3>
      <p class="page-transition-message">Please wait while we prepare your content...</p>
      <div class="page-transition-progress">
        <div class="page-transition-progress-bar"></div>
      </div>
      <p class="page-transition-destination"></p>
    </div>
  `

  // Add the overlay and top progress bar to the body
  document.body.appendChild(overlay)
  document.body.appendChild(topProgress)

  // Get references to elements
  const progressBar = overlay.querySelector(".page-transition-progress-bar")
  const destinationText = overlay.querySelector(".page-transition-destination")
  const titleElement = overlay.querySelector(".page-transition-title")

  // Function to show the loading animation
  function showPageTransition(pageName) {
    // Update the destination text
    destinationText.textContent = `Navigating to ${pageName}...`
    titleElement.textContent = `Loading ${pageName}`

    // Show the overlay
    overlay.classList.add("active")

    // Reset and animate the progress bar
    progressBar.style.width = "0%"
    topProgress.style.width = "0%"

    // Animate the progress bar
    setTimeout(() => {
      progressBar.style.width = "30%"
      topProgress.style.width = "30%"
    }, 100)

    setTimeout(() => {
      progressBar.style.width = "60%"
      topProgress.style.width = "60%"
    }, 400)

    setTimeout(() => {
      progressBar.style.width = "80%"
      topProgress.style.width = "80%"
    }, 800)
  }

  // Function to hide the loading animation
  function hidePageTransition() {
    // Complete the progress bar
    progressBar.style.width = "100%"
    topProgress.style.width = "100%"

    // Hide the overlay after a short delay
    setTimeout(() => {
      overlay.classList.remove("active")

      // Reset the progress bar after the transition
      setTimeout(() => {
        progressBar.style.width = "0%"
        topProgress.style.width = "0%"
      }, 300)
    }, 500)
  }

  // Add click event listeners to all navigation links
  const navLinks = document.querySelectorAll(".sidebar-nav a, .dropdown-content a")
  navLinks.forEach((link) => {
    link.addEventListener("click", function (e) {
      // Don't show transition for logout links
      if (this.classList.contains("logout-link") || this.classList.contains("logout-btn")) {
        return
      }

      // Get the page name from the link text or fallback to "Page"
      const pageName =
        this.querySelector("span:not(.nav-icon)")?.textContent.trim() || this.textContent.trim() || "Page"

      // Show the loading animation
      showPageTransition(pageName)
    })
  })

  // Hide the loading animation when the page has loaded
  window.addEventListener("load", hidePageTransition)

  // If the page is already loaded, hide the animation
  if (document.readyState === "complete") {
    hidePageTransition()
  }
})
