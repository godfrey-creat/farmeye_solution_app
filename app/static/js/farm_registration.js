// Section Controller for managing collapsible sections
class SectionController {
  constructor(sectionId, editBtnId, visibilityBtnId, defaultCollapsed = true) {
    this.section = document.getElementById(sectionId);
    this.editBtn = document.getElementById(editBtnId);
    this.visibilityBtn = document.getElementById(visibilityBtnId);
    this.chevronIcon = this.visibilityBtn?.querySelector("i");
    this.isVisible = !defaultCollapsed;
    this.isEditing = false;

    this.initialize();
  }

  initialize() {
    if (!this.section || !this.visibilityBtn) return;

    // Set initial state
    this.section.style.transition =
      "max-height 0.3s ease-in-out, opacity 0.3s ease-in-out, margin 0.3s ease-in-out";
    this.updateVisibility(this.isVisible);

    // Add event listeners
    this.setupEventListeners();
  }

  setupEventListeners() {
    this.visibilityBtn.addEventListener("click", () => this.toggleVisibility());

    if (this.editBtn) {
      this.editBtn.addEventListener("click", () => this.toggleEdit());
    }
  }

  updateVisibility(visible) {
    this.isVisible = visible;
    this.chevronIcon.style.transform = this.isVisible
      ? "rotate(0deg)"
      : "rotate(-180deg)";

    requestAnimationFrame(() => {
      if (this.isVisible) {
        this.section.style.maxHeight = this.section.scrollHeight + "px";
        this.section.style.opacity = "1";
        this.section.style.marginTop = "0.75rem";
      } else {
        this.section.style.maxHeight = "0";
        this.section.style.opacity = "0";
        this.section.style.marginTop = "0";
      }
    });
  }

  toggleVisibility() {
    this.updateVisibility(!this.isVisible);

    // If closing while editing, save changes
    if (!this.isVisible && this.isEditing && this.editBtn) {
      this.toggleEdit();
    }
  }

  toggleEdit() {
    if (!this.editBtn) return;

    this.isEditing = !this.isEditing;

    if (this.isEditing) {
      // Enable editing and ensure section is visible
      this.updateVisibility(true);
      this.editBtn.innerHTML = '<i class="fas fa-save mr-1"></i> Save';
      this.editBtn.classList.remove("bg-blue-600", "hover:bg-blue-700");
      this.editBtn.classList.add("bg-green-600", "hover:bg-green-700");

      this.section.querySelectorAll("input").forEach((input) => {
        input.removeAttribute("readonly");
        input.classList.remove("border-gray-300");
        input.classList.add("border-blue-400", "ring-1", "ring-blue-200");
      });
    } else {
      // Save changes when toggling edit mode off
      const formManager = window.formManager;
      if (formManager && this.section.id === "manager-info") {
        const data = {
          firstName: this.section.querySelector("#first_name").value,
          lastName: this.section.querySelector("#last_name").value,
          email: this.section.querySelector("#email").value,
        };
        formManager.updateManagerInfo(data);
      }

      // Disable editing
      this.editBtn.innerHTML = '<i class="fas fa-edit mr-1"></i> Edit';
      this.editBtn.classList.remove("bg-green-600", "hover:bg-green-700");
      this.editBtn.classList.add("bg-blue-600", "hover:bg-blue-700");

      this.section.querySelectorAll("input").forEach((input) => {
        input.setAttribute("readonly", true);
        input.classList.remove("border-blue-400", "ring-1", "ring-blue-200");
        input.classList.add("border-gray-300");
      });
    }
  }
}

// Use the working controller from the version you had
class FarmRegistrationController {
  calculateFieldArea(boundaries) {
    if (boundaries.length < 3) return 0;

    // Convert to radians
    const toRad = (deg) => (deg * Math.PI) / 180;

    // Shoelace formula for spherical earth
    let area = 0;
    const R = 6371000; // Earth radius in meters

    for (let i = 0; i < boundaries.length; i++) {
      const j = (i + 1) % boundaries.length;
      const lat1 = toRad(boundaries[i].lat);
      const lat2 = toRad(boundaries[j].lat);
      const lon1 = toRad(boundaries[i].lng);
      const lon2 = toRad(boundaries[j].lng);

      area += (lon2 - lon1) * (2 + Math.sin(lat1) + Math.sin(lat2));
    }

    area = Math.abs((area * R * R) / 2);
    return area / 10000; // Convert to hectares
  }

  async getLocationFromCoordinates(lat, lng) {
    try {
      const response = await fetch(
        `https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lng}&zoom=10&addressdetails=1`
      );
      const data = await response.json();

      // Extract more specific location information
      if (data.address) {
        // Try to get the most relevant location name
        const location =
          data.address.village ||
          data.address.town ||
          data.address.city ||
          data.address.county ||
          data.address.state_district ||
          data.address.state;
        return location || data.display_name;
      }

      return data.display_name || "Unknown Location";
    } catch (error) {
      console.error("Geocoding error:", error);
      return null; // Return null to indicate failure
    }
  }

  constructor() {
    this.teamMembers = [];
    this.farms = [];
    this.currentModalType = null;
    this.currentModalData = null;

    this.createModal();
    this.initializeEventListeners();
    this.initializeSectionControllers();
    this.initializeSampleData();
    this.setupFormSubmission();
    this.loadExistingFarms();
  }

  // Add these methods to your class
  showSuccess(title, message) {
    document.getElementById("success-message").textContent = message;
    document.getElementById("success-modal").classList.remove("hidden");
    setTimeout(() => {
      window.location.href = "/farm/dashboard";
    }, 5000);
  }

  showError(title, message) {
    document.getElementById("error-title").textContent = title;
    document.getElementById("error-message").innerHTML = message;
    document.getElementById("error-modal").classList.remove("hidden");
  }

  initializeEventListeners() {
    const addTeamMemberBtn = document.getElementById("add-team-member");
    const addFarmBtn = document.getElementById("add-farm");

    if (addTeamMemberBtn) {
      addTeamMemberBtn.addEventListener("click", () => {
        this.openModal("team-member");
      });
    }

    if (addFarmBtn) {
      addFarmBtn.addEventListener("click", () => {
        this.openModal("farm");
      });
    }

    // Call the setup method
    this.setupModalHandlers();
  }

  setupModalHandlers() {
    const closeSuccessBtn = document.getElementById("close-success");
    const closeErrorBtn = document.getElementById("close-error");

    if (closeSuccessBtn) {
      closeSuccessBtn.addEventListener("click", () => {
        document.getElementById("success-modal").classList.add("hidden");
        window.location.href = "/farm/dashboard";
      });
    }

    if (closeErrorBtn) {
      closeErrorBtn.addEventListener("click", () => {
        document.getElementById("error-modal").classList.add("hidden");
      });
    }
  }

  if(submitFormBtn) {
    submitFormBtn.addEventListener("click", () => {
      this.submitForm();
    });
  }

  if(closeSuccessBtn) {
    closeSuccessBtn.addEventListener("click", () => {
      document.getElementById("success-modal")?.classList.add("hidden");
    });
  }

  if(closeErrorBtn) {
    closeErrorBtn.addEventListener("click", () => {
      document.getElementById("error-modal")?.classList.add("hidden");
    });
  }

  initializeSectionControllers() {
    // Initialize section controllers
    new SectionController(
      "manager-info",
      "toggle-manager-edit",
      "toggle-manager-visibility",
      true // Start collapsed
    );

    new SectionController(
      "farms",
      null,
      "toggle-farm-visibility",
      true // Start collapsed
    );

    new SectionController(
      "team-members",
      null,
      "toggle-team-visibility",
      true // Start collapsed
    );
  }

  initializeSampleData() {
    // Don't add sample data by default in production
    // Only add if specifically requested
    if (false) {
      this.addTeamMemberRow();
      this.addFarmSection();
    }
  }

  // Add new team member row
  addTeamMemberRow() {
    const teamMember = {
      id: Date.now().toString(),
      firstName: "",
      lastName: "",
      email: "",
      role: "Laborer",
    };
    const row = this.createTeamMemberRow(teamMember);
    document.getElementById("team-members").appendChild(row);
    this.teamMembers.push(teamMember);
  }

  // Create team member row HTML
  createTeamMemberRow(teamMember) {
    const row = document.createElement("div");
    row.className = "border border-gray-200 rounded-md p-4 mb-4";
    row.dataset.id = teamMember.id;
    row.innerHTML = `
            <div class="flex justify-between items-center">
                <div class="flex-1 grid grid-cols-4 gap-4">
                    <div class="text-sm text-gray-600">${teamMember.firstName}</div>
                    <div class="text-sm text-gray-600">${teamMember.lastName}</div>
                    <div class="text-sm text-gray-600">${teamMember.email}</div>
                    <div class="text-sm text-gray-600">${teamMember.role}</div>
                </div>
                <div class="flex space-x-2">
                    <button class="edit-team-member bg-blue-600 hover:bg-blue-700 text-white px-3 py-1 rounded-md text-sm flex items-center">
                        <i class="fas fa-edit mr-1"></i> Edit
                    </button>
                    <button class="remove-team-member bg-red-600 hover:bg-red-700 text-white px-3 py-1 rounded-md text-sm flex items-center">
                        <i class="fas fa-trash-alt mr-1"></i> Remove
                    </button>
                </div>
            </div>
        `;

    // Add event listener for remove button
    row.querySelector(".remove-team-member").addEventListener("click", () => {
      if (confirm("Are you sure you want to remove this team member?")) {
        row.remove();
        this.teamMembers = this.teamMembers.filter(
          (member) => member.id !== teamMember.id
        );
      }
    });

    // Add event listener for edit button
    row.querySelector(".edit-team-member").addEventListener("click", () => {
      this.openModal("team-member", teamMember);
    });

    return row;
  }

  // Modal handling methods
  createModal() {
    const modalHTML = `
            <div id="reusable-modal" class="fixed inset-0 bg-gray-600 bg-opacity-50 hidden overflow-y-auto h-full w-full z-50">
                <div class="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
                    <div class="mt-3">
                        <h3 id="modal-title" class="text-lg leading-6 font-medium text-gray-900"></h3>
                        <form id="modal-form" class="mt-4">
                            <div id="modal-content" class="mt-2">
                                <!-- Form fields will be injected here -->
                            </div>
                            <div class="flex justify-end space-x-3 mt-4">
                                <button type="button" id="modal-cancel" class="bg-gray-500 text-white px-4 py-2 rounded-md hover:bg-gray-600 text-sm">
                                    Cancel
                                </button>
                                <button type="submit" id="modal-save" class="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 text-sm">
                                    Save
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            </div>
        `;

    document.body.insertAdjacentHTML("beforeend", modalHTML);

    // Add event listeners
    const modal = document.getElementById("reusable-modal");
    const modalForm = document.getElementById("modal-form");
    const cancelBtn = document.getElementById("modal-cancel");

    cancelBtn.addEventListener("click", () => this.closeModal());
    modal.addEventListener("click", (e) => {
      if (e.target === modal) this.closeModal();
    });

    modalForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      await this.handleModalSave();
    });
  }

  openModal(type, data = null) {
    const modal = document.getElementById("reusable-modal");
    const modalTitle = document.getElementById("modal-title");
    const modalContent = document.getElementById("modal-content");

    this.currentModalType = type;
    this.currentModalData = data;

    // Set title and content based on type
    if (type === "team-member") {
      modalTitle.textContent = data ? "Edit Team Member" : "Add Team Member";
      modalContent.innerHTML = this.getTeamMemberForm(data);
    } else if (type === "farm") {
      modalTitle.textContent = data ? "Edit Farm" : "Add Farm";
      modalContent.innerHTML = this.getFarmForm(data);
      this.initializeFarmForm();
    }

    modal.classList.remove("hidden");
  }

  closeModal() {
    const modal = document.getElementById("reusable-modal");
    modal.classList.add("hidden");
    this.currentModalType = null;
    this.currentModalData = null;
  }

  getTeamMemberForm(data = null) {
    return `
            <div class="space-y-4">
                <div>
                    <label class="block text-sm font-medium text-gray-700">First Name</label>
                    <input type="text" name="firstName" class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                        value="${data ? data.firstName : ""}" required>
                </div>
                <div>
                    <label class="block text-sm font-medium text-gray-700">Last Name</label>
                    <input type="text" name="lastName" class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                        value="${data ? data.lastName : ""}" required>
                </div>
                <div>
                    <label class="block text-sm font-medium text-gray-700">Email</label>
                    <input type="email" name="email" class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                        value="${data ? data.email : ""}" required>
                </div>
                <div>
                    <label class="block text-sm font-medium text-gray-700">Role</label>
                    <select name="role" class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500">
                        ${this.getRoleOptions(data ? data.role : "Laborer")}
                    </select>
                </div>
            </div>
        `;
  }

  getRoleOptions(selected) {
    const roles = [
      "Laborer",
      "Farm Guide",
      "Harvester",
      "Irrigator",
      "Planter",
      "Weeder",
    ];
    return roles
      .map(
        (role) =>
          `<option value="${role}" ${
            role === selected ? "selected" : ""
          }>${role}</option>`
      )
      .join("");
  }

  getFarmForm(data = null) {
    return `
            <div class="space-y-4">
                <div>
                    <label class="block text-sm font-medium text-gray-700">Farm Name</label>
                    <input type="text" name="farmName" class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                        value="${data ? data.name : ""}" required>
                </div>                <div>
                    <label class="block text-sm font-medium text-gray-700">Region</label>
                    <select name="region" class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500" required>
                        <option value="nairobi" ${
                          data && data.region === "nairobi" ? "selected" : ""
                        }>Nairobi</option>
                        <option value="central" ${
                          data && data.region === "central" ? "selected" : ""
                        }>Central</option>
                        <option value="coast" ${
                          data && data.region === "coast" ? "selected" : ""
                        }>Coast</option>
                        <option value="eastern" ${
                          data && data.region === "eastern" ? "selected" : ""
                        }>Eastern</option>
                        <option value="north-eastern" ${
                          data && data.region === "north-eastern"
                            ? "selected"
                            : ""
                        }>North Eastern</option>
                        <option value="nyanza" ${
                          data && data.region === "nyanza" ? "selected" : ""
                        }>Nyanza</option>
                        <option value="rift-valley" ${
                          data && data.region === "rift-valley"
                            ? "selected"
                            : ""
                        }>Rift Valley</option>
                        <option value="western" ${
                          data && data.region === "western" ? "selected" : ""
                        }>Western</option>
                    </select>
                </div>

                <!-- Fields Section -->
                <div id="fields-section" class="space-y-4">
                    <div class="flex justify-between items-center">
                        <h4 class="text-md font-medium text-gray-700">Fields</h4>
                        <button type="button" id="add-field-btn" class="bg-green-600 hover:bg-green-700 text-white px-3 py-1 rounded-md text-sm flex items-center">
                            <i class="fas fa-plus mr-1"></i> Add Field
                        </button>
                    </div>
                    
                    <div id="fields-container" class="space-y-4">
                        <!-- Field entries will be added here -->
                    </div>
                </div>
            </div>

            <template id="field-template">
                <div class="field-entry border rounded-md p-4 bg-gray-50">
                    <div class="flex justify-between items-start mb-4">
                        <div class="flex-1 space-y-4">
                            <div>
                                <label class="block text-sm font-medium text-gray-700">Field Name</label>
                                <input type="text" name="fieldName" class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500" required>
                            </div>
                            <div>
                                <label class="block text-sm font-medium text-gray-700">Crop Type</label>
                                <select name="cropType" class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500">
                                    <option value="">Select a crop type</option>
                                    <option value="Corn">Corn</option>
                                    <option value="Soybeans">Soybeans</option>
                                    <option value="Wheat">Wheat</option>
                                    <option value="Cotton">Cotton</option>
                                    <option value="Rice">Rice</option>
                                </select>
                            </div>
                            <div>
                <label class="block text-sm font-medium text-gray-700">Water Source</label>
                <select name="waterSource" class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500" required>
                    <option value="">Select water source</option>
                    <option value="River">River</option>
                    <option value="Well">Well</option>
                    <option value="Borehole">Borehole</option>
                    <option value="Dam">Dam/Reservoir</option>
                    <option value="Rainwater">Rainwater Harvesting</option>
                    <option value="Municipal">Municipal Supply</option>
                </select>
            </div>

            <div>
                <label class="block text-sm font-medium text-gray-700">Irrigation Type</label>
                <select name="irrigationType" class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500" required>
                    <option value="">Select irrigation type</option>
                    <option value="Drip">Drip Irrigation</option>
                    <option value="Sprinkler">Sprinkler</option>
                    <option value="Flood">Flood/Furrow</option>
                    <option value="Center Pivot">Center Pivot</option>
                    <option value="Rain-fed">Rain-fed (No irrigation)</option>
                </select>
            </div>
                        </div>
                        <button type="button" class="remove-field-btn text-red-600 hover:text-red-800 ml-2">
                            <i class="fas fa-times"></i>
                        </button>
                    </div>

                    

                    <!-- Boundary Markers Section -->
                    <div class="boundary-markers-section mt-4">
                        <div class="flex justify-between items-center mb-2">
                            <h5 class="text-sm font-medium text-gray-700">Boundary Markers</h5>
                            <button type="button" class="add-marker-btn bg-blue-600 hover:bg-blue-700 text-white px-2 py-1 rounded text-xs flex items-center">
                                <i class="fas fa-plus mr-1"></i> Add Marker
                            </button>
                        </div>
                        <p class="text-xs text-gray-500 mb-2">Add at least 3 markers to define the field boundaries</p>
                        <div class="markers-container space-y-3">
                            <!-- Markers will be added here -->
                        </div>
                    </div>
                    <div>
                <label class="block text-sm font-medium text-gray-700">Description</label>
                <textarea name="description" rows="3" class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                    placeholder="Brief description of your farm">${
                      data ? data.description : ""
                    }</textarea>
            </div>
                </div>
            </template>

            <template id="marker-template">
                <div class="marker-entry grid grid-cols-3 gap-2 items-end">
                    <div>
                        <label class="block text-xs font-medium text-gray-700">Latitude</label>
                        <input type="number" step="any" name="latitude" class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 text-sm" placeholder="e.g. 40.7128" required>
                    </div>
                    <div>
                        <label class="block text-xs font-medium text-gray-700">Longitude</label>
                        <input type="number" step="any" name="longitude" class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 text-sm" placeholder="e.g. -74.0060" required>
                    </div>
                    <div class="flex space-x-1">
                        <button type="button" class="get-location-btn bg-blue-600 hover:bg-blue-700 text-white px-2 py-1 rounded text-xs">
                            <i class="fas fa-location-arrow"></i>
                        </button>
                        <button type="button" class="remove-marker-btn bg-red-600 hover:bg-red-700 text-white px-2 py-1 rounded text-xs">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </div>
            </template>
        `;
  }

  // Add event listeners after the farm form is created
  initializeFarmForm() {
    const fieldsContainer = document.getElementById("fields-container");
    const addFieldBtn = document.getElementById("add-field-btn");
    const fieldTemplate = document.getElementById("field-template");
    const markerTemplate = document.getElementById("marker-template");

    if (addFieldBtn) {
      addFieldBtn.addEventListener("click", () => {
        const fieldEntry = fieldTemplate.content.cloneNode(true);
        const field = fieldEntry.querySelector(".field-entry");

        // Add event listener for remove field button
        field
          .querySelector(".remove-field-btn")
          .addEventListener("click", () => {
            field.remove();
          });

        // Add event listener for add marker button
        field.querySelector(".add-marker-btn").addEventListener("click", () => {
          const markerEntry = markerTemplate.content.cloneNode(true);
          const marker = markerEntry.querySelector(".marker-entry");

          // Add event listeners for marker buttons
          marker
            .querySelector(".get-location-btn")
            .addEventListener("click", () => {
              const latInput = marker.querySelector('[name="latitude"]');
              const lngInput = marker.querySelector('[name="longitude"]');
              this.getCurrentLocation(latInput, lngInput);
            });

          marker
            .querySelector(".remove-marker-btn")
            .addEventListener("click", () => {
              marker.remove();
            });

          field.querySelector(".markers-container").appendChild(marker);
        });

        fieldsContainer.appendChild(field);
      });
    }
  }

  async handleModalSave() {
    const formData = new FormData(document.getElementById("modal-form"));
    console.log("Form data entries:", Array.from(formData.entries()));
    const data = Object.fromEntries(formData.entries());
    console.log("Converted form data:", data);

    if (this.currentModalType === "team-member") {
      if (this.currentModalData) {
        // Update existing team member
        const member = this.teamMembers.find(
          (m) => m.id === this.currentModalData.id
        );
        if (member) {
          Object.assign(member, {
            firstName: data.firstName,
            lastName: data.lastName,
            email: data.email,
            role: data.role,
          });
          // Update the row in the UI
          const row = document.querySelector(`[data-id="${member.id}"]`);
          if (row) {
            row.replaceWith(this.createTeamMemberRow(member));
          }
        }
      } else {
        // Add new team member
        const newMember = {
          id: Date.now().toString(),
          firstName: data.firstName,
          lastName: data.lastName,
          email: data.email,
          role: data.role,
        };
        this.teamMembers.push(newMember);
        document
          .getElementById("team-members")
          .appendChild(this.createTeamMemberRow(newMember));
      }
    } else if (this.currentModalType === "farm") {
      const modalForm = document.getElementById("modal-form");
      const farmData = Object.fromEntries(formData.entries());
      console.log("Farm Data from Modal:", farmData);
      console.log("Farm Name specifically:", farmData.farmName);

      // Collect fields directly here
      const fields = [];
      const fieldEntries = modalForm.querySelectorAll(".field-entry");
      console.log("Number of field entries found:", fieldEntries.length);

      fieldEntries.forEach((fieldEntry, index) => {
        const fieldNameInput = fieldEntry.querySelector(
          'input[name="fieldName"]'
        );
        const fieldName = fieldNameInput?.value;

        console.log(`Field ${index} - Name:`, fieldName);

        if (!fieldName || fieldName.trim() === "") {
          console.log(`Field ${index} skipped - no name`);
          return;
        }

        // Get crop type for this field
        const cropTypeSelect = fieldEntry.querySelector(
          'select[name="cropType"]'
        );
        const cropType = cropTypeSelect?.value || "";

        const boundaries = [];
        const markersContainer = fieldEntry.querySelector(".markers-container");
        const markerEntries =
          markersContainer?.querySelectorAll(".marker-entry") || [];

        console.log(
          `Field ${index} - Number of markers:`,
          markerEntries.length
        );

        markerEntries.forEach((markerEntry, markerIndex) => {
          const latInput = markerEntry.querySelector('input[name="latitude"]');
          const lngInput = markerEntry.querySelector('input[name="longitude"]');

          const lat = latInput?.value;
          const lng = lngInput?.value;

          console.log(
            `Field ${index}, Marker ${markerIndex} - Lat: ${lat}, Lng: ${lng}`
          );

          if (lat && lng) {
            boundaries.push({
              lat: parseFloat(lat),
              lng: parseFloat(lng),
            });
          }
        });

        // Only add field if it has at least 3 boundaries
        if (boundaries.length >= 3) {
          fields.push({
            id: Date.now().toString() + Math.random(),
            name: fieldName,
            cropType: cropType,
            boundaries: boundaries,
          });
          console.log(
            `Field ${index} added with ${boundaries.length} boundaries`
          );
        } else {
          console.log(
            `Field ${index} skipped - only ${boundaries.length} boundaries (minimum 3 required)`
          );
        }
      });

      console.log("Total fields collected:", fields.length);

      // Calculate total farm area from all fields
      let totalArea = 0;
      fields.forEach((field) => {
        totalArea += this.calculateFieldArea(field.boundaries);
      });
      console.log("Total farm area calculated:", totalArea, "hectares");

      // Get center coordinates for geocoding
      let centerLat = 0,
        centerLng = 0,
        coordCount = 0;
      fields.forEach((field) => {
        field.boundaries.forEach((boundary) => {
          centerLat += boundary.lat;
          centerLng += boundary.lng;
          coordCount++;
        });
      });

      if (coordCount > 0) {
        centerLat /= coordCount;
        centerLng /= coordCount;
      }

      // Get location name from coordinates
      let locationName = farmData.region; // Default to region
      if (centerLat && centerLng) {
        try {
          const geocodedLocation = await this.getLocationFromCoordinates(
            centerLat,
            centerLng
          );
          if (geocodedLocation) {
            locationName = geocodedLocation;
            console.log("Geocoded location:", locationName);
          }
        } catch (error) {
          console.error("Failed to geocode location:", error);
          // Fall back to region if geocoding fails
        }
      }

      // Get the first field's crop type for the farm's primary crop
      const primaryCropType =
        fields.length > 0 && fields[0].cropType ? fields[0].cropType : "Mixed";

      if (this.currentModalData) {
        // Update existing farm
        const farm = this.farms.find((f) => f.id === this.currentModalData.id);
        if (farm) {
          farm.name = farmData.farmName;
          farm.region = farmData.region;
          farm.location = locationName;
          farm.description = farmData.description || "";
          farm.waterSource = farmData.waterSource;
          farm.irrigationType = farmData.irrigationType;
          farm.size = totalArea;
          farm.size_acres = totalArea * 2.47105; // Convert hectares to acres
          farm.latitude = centerLat;
          farm.longitude = centerLng;
          farm.cropType = primaryCropType;
          farm.fields = fields;
          console.log("Updated farm:", farm);
        }
      } else {
        // Add new farm
        const newFarm = {
          id: Date.now().toString(),
          name: farmData.farmName,
          region: farmData.region,
          location: locationName,
          description: farmData.description || "",
          waterSource: farmData.waterSource,
          irrigationType: farmData.irrigationType,
          size: totalArea,
          size_acres: totalArea * 2.47105,
          latitude: centerLat,
          longitude: centerLng,
          cropType: primaryCropType,
          fields: fields,
        };
        console.log("Adding new farm with geocoded location:", newFarm);
        this.farms.push(newFarm);
      }

      console.log("All farms after update:", this.farms);
      this.renderFarms();
    }

    this.closeModal();
  }

  addFarmSection() {
    const farm = {
      id: Date.now().toString(),
      name: "",
      region:
        document.querySelector("#current-user-region")?.value || "nairobi", // Default to user's region
      fields: [],
    };
    this.farms.push(farm);
    this.renderFarms();
    this.openModal("farm", farm);
  }

  // Create farm section HTML
  createFarmSection(farm) {
    const section = document.createElement("div");
    section.className = "border border-gray-200 rounded-md p-4";
    section.dataset.id = farm.id;
    section.innerHTML = `
            <div class="mb-4">
                <h3 class="text-lg font-medium text-gray-800">Farm Details</h3>
            </div>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                <div>
                    <label class="block text-sm font-medium text-gray-700">Farm Name</label>
                    <input type="text" class="farm-name mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500" required>
                </div>
                <div>                    <label class="block text-sm font-medium text-gray-700">Region</label>
                    <select class="farm-region mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500" required>
                        <option value="nairobi">Nairobi</option>
                        <option value="central">Central</option>
                        <option value="coast">Coast</option>
                        <option value="eastern">Eastern</option>
                        <option value="north-eastern">North Eastern</option>
                        <option value="nyanza">Nyanza</option>
                        <option value="rift-valley">Rift Valley</option>
                        <option value="western">Western</option>
                    </select>
                </div>
            </div>
            <div class="mb-4">
                <div class="flex justify-between items-center">
                    <h4 class="font-medium text-gray-700">Fields</h4>
                    <button class="add-field bg-green-600 hover:bg-green-700 text-white px-3 py-1 rounded-md text-sm flex items-center">
                        <i class="fas fa-plus mr-1"></i> Add Field
                    </button>
                </div>
                <div class="fields mt-4 space-y-4">
                    <!-- Field sections will be added here -->
                </div>
            </div>
            
            <div class="flex justify-end">
                <button class="remove-farm bg-red-600 hover:bg-red-700 text-white px-3 py-1 rounded-md text-sm flex items-center">
                    <i class="fas fa-trash-alt mr-1"></i> Remove Farm
                </button>
            </div>
        `;

    // Set initial values
    section.querySelector(".farm-name").value = farm.name;
    section.querySelector(".farm-region").value = farm.region;

    // Add event listener for remove button
    section.querySelector(".remove-farm").addEventListener("click", () => {
      if (
        confirm("Are you sure you want to remove this farm and all its fields?")
      ) {
        section.remove();
        this.farms = this.farms.filter((f) => f.id !== farm.id);
      }
    });

    // Add field button
    section.querySelector(".add-field").addEventListener("click", () => {
      this.addField(section, farm);
    });
    // Add input and select change listeners
    const inputs = section.querySelectorAll("input, select");
    inputs.forEach((input) => {
      input.addEventListener("change", (e) => {
        const currentFarm = this.farms.find((f) => f.id === farm.id);
        if (currentFarm) {
          if (e.target.classList.contains("farm-name"))
            currentFarm.name = e.target.value;
          if (e.target.classList.contains("farm-region"))
            currentFarm.region = e.target.value;
        }
      });
    });

    return section;
  }

  // Add field to farm
  addField(farmSection, farm) {
    const field = {
      id: Date.now().toString(),
      name: "",
      boundaries: [],
    };
    const fieldSection = this.createFieldSection(field, farmSection, farm);
    farmSection.querySelector(".fields").appendChild(fieldSection);
    farm.fields.push(field);
  }

  // Add boundary marker to field
  addBoundaryMarker(fieldSection, field) {
    const marker = {
      id: Date.now().toString(),
      lat: "",
      lng: "",
    };
    const markerRow = this.createBoundaryMarkerRow(marker, fieldSection, field);
    fieldSection.querySelector(".boundary-markers").appendChild(markerRow);
    field.boundaries.push(marker);
  }

  // Get current location
  getCurrentLocation(latInput, lngInput, marker) {
    if (navigator.geolocation) {
      latInput.disabled = true;
      lngInput.disabled = true;

      // Show loading state
      const button =
        latInput.parentElement.parentElement.querySelector(".get-location");
      const originalHTML = button.innerHTML;
      button.innerHTML =
        '<i class="fas fa-spinner fa-spin mr-1"></i> Locating...';
      button.disabled = true;

      navigator.geolocation.getCurrentPosition(
        (position) => {
          latInput.value = position.coords.latitude.toFixed(6);
          lngInput.value = position.coords.longitude.toFixed(6);
          marker.lat = latInput.value;
          marker.lng = lngInput.value;

          // Restore button
          button.innerHTML = originalHTML;
          button.disabled = false;
          latInput.disabled = false;
          lngInput.disabled = false;
        },
        (error) => {
          console.error("Error getting location:", error);
          alert(
            "Could not get your current location. Please enter coordinates manually."
          );

          // Restore button
          button.innerHTML = originalHTML;
          button.disabled = false;
          latInput.disabled = false;
          lngInput.disabled = false;
        }
      );
    } else {
      alert(
        "Geolocation is not supported by your browser. Please enter coordinates manually."
      );
    }
  }

  // Validate form data
  validateForm() {
    console.log("Starting validation. Current farms:", this.farms);
    let isValid = true;
    const errors = [];

    // Validate team members
    if (this.teamMembers.length === 0) {
      errors.push("Please add at least one team member");
      isValid = false;
    } else {
      this.teamMembers.forEach((member, index) => {
        if (!member.firstName || !member.lastName || !member.email) {
          errors.push(`Team member ${index + 1} is missing required fields`);
          isValid = false;
        }

        // Simple email validation
        if (member.email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(member.email)) {
          errors.push(`Team member ${index + 1} has an invalid email address`);
          isValid = false;
        }
      });
    }

    // Validate farms
    if (this.farms.length === 0) {
      errors.push("Please add at least one farm");
      isValid = false;
    } else {
      this.farms.forEach((farm, farmIndex) => {
        if (!farm.name) {
          errors.push(`Farm ${farmIndex + 1} is missing a name`);
          isValid = false;
        }

        // Validate fields
        if (farm.fields.length === 0) {
          errors.push(`Farm "${farm.name}" has no fields`);
          isValid = false;
        } else {
          farm.fields.forEach((field, fieldIndex) => {
            if (!field.name) {
              errors.push(
                `Field ${fieldIndex + 1} in farm "${
                  farm.name
                }" is missing a name`
              );
              isValid = false;
            }

            // Validate boundary markers
            if (field.boundaries.length < 3) {
              errors.push(
                `Field "${field.name}" in farm "${farm.name}" needs at least 3 boundary markers`
              );
              isValid = false;
            } else {
              field.boundaries.forEach((marker, markerIndex) => {
                if (!marker.lat || !marker.lng) {
                  errors.push(
                    `Boundary marker ${markerIndex + 1} in field "${
                      field.name
                    }" is missing coordinates`
                  );
                  isValid = false;
                }
              });
            }
          });
        }
      });
    }

    if (!isValid) {
      this.showError("Validation Error", errors.join("<br>"));
    }

    return isValid;
  }

  // Show error message
  showError(title, message) {
    document.getElementById("error-title").textContent = title;
    document.getElementById("error-message").innerHTML = message;
    document.getElementById("error-modal").classList.remove("hidden");
  }

  // Submit form data
  async submitForm() {
    console.log("=== FORM SUBMISSION STARTED ===");
    console.log("Current farms before validation:", this.farms);

    if (!this.validateForm()) {
      console.log("Form validation failed");
      return;
    }

    // Get CSRF token
    const csrfToken = document.querySelector('input[name="csrf_token"]').value;
    console.log("CSRF Token:", csrfToken);

    // Prepare form data
    const formData = {
      teamMembers: this.teamMembers.map((member) => ({
        firstName: member.firstName,
        lastName: member.lastName,
        email: member.email,
        role: member.role,
      })),
      farms: this.farms.map((farm) => ({
        name: farm.name,
        region: farm.region,
        location: farm.location,
        description: farm.description,
        waterSource: farm.waterSource,
        irrigationType: farm.irrigationType,
        size: farm.size,
        size_acres: farm.size_acres,
        latitude: farm.latitude,
        longitude: farm.longitude,
        cropType: farm.cropType,
        fields: farm.fields.map((field) => ({
          name: field.name,
          cropType: field.cropType,
          boundaries: field.boundaries.map((boundary) => ({
            lat: boundary.lat,
            lng: boundary.lng,
          })),
        })),
      })),
    };

    console.log("=== FORM DATA BEING SUBMITTED ===");
    console.log(JSON.stringify(formData, null, 2));

    const requestUrl = "/farm/register";

    // Show loading state on submit button
    const submitButton = document.querySelector('button[type="submit"]');
    const originalHTML = submitButton.innerHTML;
    submitButton.innerHTML =
      '<i class="fas fa-spinner fa-spin mr-2"></i> Processing...';
    submitButton.disabled = true;

    try {
      console.log("Sending request to server...");
      const response = await fetch(requestUrl, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": csrfToken,
        },
        body: JSON.stringify(formData),
        credentials: "same-origin",
      });

      console.log("=== SERVER RESPONSE ===");
      console.log("Response Status:", response.status);
      console.log("Response OK:", response.ok);

      const responseData = await response.json();
      console.log("Response Data:", responseData);

      if (response.ok && responseData.success) {
        console.log("=== SUBMISSION SUCCESSFUL ===");
        this.showSuccess(
          "Registration Successful",
          responseData.message ||
            "Your farm has been registered successfully. Redirecting to dashboard..."
        );
      } else {
        // Handle error response
        throw new Error(responseData.error || "Registration failed");
      }
    } catch (error) {
      console.error("=== SUBMISSION ERROR ===");
      console.error("Error:", error);
      this.showError(
        "Registration Failed",
        error.message ||
          "There was an error submitting your farm registration. Please try again."
      );
    } finally {
      // Restore button
      submitButton.innerHTML = originalHTML;
      submitButton.disabled = false;
      console.log("=== FORM SUBMISSION COMPLETED ===");
    }
  }

  setupFormSubmission() {
    const form = document.getElementById("farm-form");
    if (form) {
      form.addEventListener("submit", async (e) => {
        e.preventDefault();
        await this.submitForm(form);
      });
    }
  }

  async loadExistingFarms() {
    try {
      const response = await fetch("/farm/get_farms", {
        method: "GET",
        headers: {
          Accept: "application/json",
        },
      });

      if (response.ok) {
        const data = await response.json();
        if (data.success && data.farms) {
          this.farms = data.farms;
          this.renderFarms();
        }
      }
    } catch (error) {
      console.error("Error loading existing farms:", error);
    }
  }

  renderFarms() {
    const farmsContainer = document.getElementById("farms");
    const emptyMessage = document.getElementById("empty-farms-message");

    if (!farmsContainer) return;

    // Clear existing content
    farmsContainer
      .querySelectorAll(".farm-entry")
      .forEach((entry) => entry.remove());

    if (!this.farms || this.farms.length === 0) {
      // Show empty state message
      emptyMessage?.classList.remove("hidden");
      return;
    }

    // Hide empty state message if farms exist
    emptyMessage?.classList.add("hidden");

    // Get template
    const template = document.getElementById("farm-entry-template");
    if (!template) return;

    // Add each farm
    this.farms.forEach((farm) => {
      const farmEntry = template.content
        .cloneNode(true)
        .querySelector(".farm-entry");

      // Set farm details
      farmEntry.querySelector(".farm-name").textContent =
        farm.name || "Unnamed Farm";
      farmEntry.querySelector(".farm-region").textContent =
        farm.region || "No Region Set";
      farmEntry.dataset.id = farm.id;

      // Add event listeners
      farmEntry.querySelector(".edit-farm").addEventListener("click", () => {
        this.openModal("farm", farm);
      });

      farmEntry.querySelector(".remove-farm").addEventListener("click", () => {
        if (
          confirm(
            "Are you sure you want to remove this farm and all its fields?"
          )
        ) {
          this.farms = this.farms.filter((f) => f.id !== farm.id);
          this.renderFarms();
        }
      });

      farmsContainer.appendChild(farmEntry);
    });
  }
}

// Remove everything after the FarmRegistrationController class and replace with this:

// Initialize everything in a single DOMContentLoaded
document.addEventListener("DOMContentLoaded", () => {
  // Check if all required elements exist
  const managerInfo = document.getElementById("manager-info");
  const teamMembers = document.getElementById("team-members");
  const farms = document.getElementById("farms");
  const farmForm = document.getElementById("farm-form");

  if (!managerInfo || !teamMembers || !farms || !farmForm) {
    console.warn("Some required elements are missing. Initialization skipped.");
    return;
  }

  // Initialize the main controller
  const controller = new FarmRegistrationController();
  console.log("Farm registration controller initialized successfully");

  // Initialize form state manager
  const formManager = new FormStateManager();
  window.formManager = formManager; // Make it available globally if needed

  // Initialize section controllers (if not already done in FarmRegistrationController)
  const sections = [
    {
      id: "manager-info",
      editBtn: "toggle-manager-edit",
      visibilityBtn: "toggle-manager-visibility",
    },
    { id: "farms", editBtn: null, visibilityBtn: "toggle-farm-visibility" },
    {
      id: "team-members",
      editBtn: null,
      visibilityBtn: "toggle-team-visibility",
    },
  ];

  sections.forEach((section) => {
    new SectionController(
      section.id,
      section.editBtn,
      section.visibilityBtn,
      true
    );
  });

  // Ensure manager inputs have gray borders by default (readonly state)
  document.querySelectorAll("#manager-info input").forEach((input) => {
    input.classList.add("border-gray-300");
  });

  // Remove the separate form submission handler since it's handled by the controller
  // The controller's setupFormSubmission() method should handle this
});

// Export the SectionController class for use in other modules
window.SectionController = SectionController;

// Simple modal utility (only if not already in the controller)
window.modalManager = {
  closeModal: (modalId) => {
    const modal = document.getElementById(modalId);
    if (modal) {
      modal.classList.add("hidden");
    }
  },

  showModal: (modalId, message = "") => {
    const modal = document.getElementById(modalId);
    if (modal) {
      if (message) {
        const messageEl = modal.querySelector(`#${modalId}-message`);
        if (messageEl) {
          messageEl.textContent = message;
        }
      }
      modal.classList.remove("hidden");
    }
  },
};