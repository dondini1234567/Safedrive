document.addEventListener("DOMContentLoaded", () => {
  // Close flash messages
  document.querySelectorAll(".flash-message .close-btn").forEach((btn) => {
    btn.addEventListener("click", function () {
      this.parentElement.style.opacity = "0"
      setTimeout(() => {
        this.parentElement.style.display = "none"
      }, 300)
    })
  })

  // Auto-hide flash messages after 5 seconds
  setTimeout(() => {
    document.querySelectorAll(".flash-message").forEach((msg) => {
      msg.style.opacity = "0"
      setTimeout(() => {
        msg.style.display = "none"
      }, 300)
    })
  }, 5000)

  // User dropdown menu
  const userAvatar = document.querySelector(".user-avatar")
  if (userAvatar) {
    userAvatar.addEventListener("click", function () {
      const dropdown = this.nextElementSibling
      dropdown.classList.toggle("show")
    })

    // Close dropdown when clicking outside
    document.addEventListener("click", (event) => {
      if (!event.target.matches(".user-avatar")) {
        const dropdowns = document.querySelectorAll(".dropdown-content")
        dropdowns.forEach((dropdown) => {
          if (dropdown.classList.contains("show")) {
            dropdown.classList.remove("show")
          }
        })
      }
    })
  }

  // Ensure logout links work properly
  document.querySelectorAll(".logout-btn, .logout-link").forEach((link) => {
    link.addEventListener("click", function (e) {
      // Don't prevent default behavior - let the link work naturally
      console.log("Logout clicked, redirecting to:", this.getAttribute("href"))
    })
  })

  // Force reload profile images to prevent caching
  function refreshProfileImages() {
    fetch("/refresh-profile-image")
      .then((response) => response.json())
      .then((data) => {
        // Update all profile images with the new URL
        document.querySelectorAll(".avatar img, .user-avatar").forEach((img) => {
          img.src = data.profile_image_url
        })
      })
      .catch((error) => console.error("Error refreshing profile image:", error))
  }

  // Refresh profile images when page loads
  refreshProfileImages()
})
