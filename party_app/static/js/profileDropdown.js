export function initProfileDropdownToggle() {
    const profileMenu = document.getElementById("profile-menu");
    const profileDropdown = document.getElementById("profile-dropdown");
    if (!profileMenu || !profileDropdown) return;
  
    profileMenu.addEventListener("click", (evt) => {
      evt.stopPropagation();
      profileMenu.classList.toggle("open");
    });
  
    profileDropdown.addEventListener("click", evt => {
      evt.stopPropagation();
    });
  
    document.addEventListener("click", (evt) => {
      const isClickInside = profileMenu.contains(evt.target);
      if (!isClickInside) {
        profileMenu.classList.remove("open");
      }
    });
  }
  