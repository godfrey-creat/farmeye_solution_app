// Rename SectionController to avoid conflicts
class FarmSectionController {
    constructor(sectionId, editBtnId, visibilityBtnId, defaultCollapsed = true) {
        this.section = document.getElementById(sectionId);
        this.editBtn = document.getElementById(editBtnId);
        this.visibilityBtn = document.getElementById(visibilityBtnId);
        this.chevronIcon = this.visibilityBtn?.querySelector('i');
        this.isVisible = !defaultCollapsed;
        this.isEditing = false;
        this.originalHeight = this.section?.scrollHeight || 0;

        this.initialize();
    }

    initialize() {
        if (!this.section || !this.visibilityBtn) return;

        // Set initial state
        if (!this.isVisible) {
            this.section.style.maxHeight = '0';
            this.section.style.opacity = '0';
            this.section.style.marginTop = '0';
            this.chevronIcon.style.transform = 'rotate(-180deg)';
        } else {
            this.section.style.maxHeight = this.originalHeight + 'px';
            this.section.style.opacity = '1';
            this.section.style.marginTop = '0.75rem';
        }

        // Add transitions
        this.section.style.transition = 'max-height 0.3s ease-in-out, opacity 0.3s ease-in-out, margin 0.3s ease-in-out';

        // Add event listeners
        this.setupEventListeners();
    }

    setupEventListeners() {
        this.visibilityBtn.addEventListener('click', () => this.toggleVisibility());

        if (this.editBtn) {
            this.editBtn.addEventListener('click', () => this.toggleEdit());
        }
    }

    updateVisibility(visible) {
        this.isVisible = visible;
        this.chevronIcon.style.transform = this.isVisible ? 'rotate(0deg)' : 'rotate(-180deg)';

        if (this.isVisible) {
            this.section.style.maxHeight = this.originalHeight + 'px';
            this.section.style.opacity = '1';
            this.section.style.marginTop = '0.75rem';
        } else {
            this.section.style.maxHeight = '0';
            this.section.style.opacity = '0';
            this.section.style.marginTop = '0';
        }
    }

    toggleVisibility() {
        this.updateVisibility(!this.isVisible);

        // If closing while editing, save changes
        if (!this.isVisible && this.isEditing && this.editBtn) {
            this.toggleEdit();
        }
    }

    toggleEdit() {
        this.isEditing = !this.isEditing;

        if (this.isEditing) {
            // Enable editing and ensure section is visible
            this.updateVisibility(true);
            this.editBtn.innerHTML = '<i class="fas fa-save mr-1"></i> Save';
            this.editBtn.classList.remove('bg-blue-600', 'hover:bg-blue-700');
            this.editBtn.classList.add('bg-green-600', 'hover:bg-green-700');

            this.section.querySelectorAll('input').forEach(input => {
                input.removeAttribute('readonly');
                input.classList.remove('border-gray-300');
                input.classList.add('border-blue-400', 'ring-1', 'ring-blue-200');
            });
        } else {
            // Disable editing
            this.editBtn.innerHTML = '<i class="fas fa-edit mr-1"></i> Edit';
            this.editBtn.classList.remove('bg-green-600', 'hover:bg-green-700');
            this.editBtn.classList.add('bg-blue-600', 'hover:bg-blue-700');

            this.section.querySelectorAll('input').forEach(input => {
                input.setAttribute('readonly', true);
                input.classList.remove('border-blue-400', 'ring-1', 'ring-blue-200');
                input.classList.add('border-gray-300');
            });
        }
    }
}

// Use the working controller from the version you had
class FarmRegistrationController {
    constructor() {
        this.teamMembers = [];
        this.farms = [];
        this.currentModalType = null;
        this.currentModalData = null;
        
        this.createModal();
        this.initializeEventListeners();
        this.initializeSectionControllers();
        this.initializeSampleData();
    }

    initializeEventListeners() {
        // Add Team Member button
        document.getElementById('add-team-member').addEventListener('click', () => {
            this.openModal('team-member');
        });
        
        // Add Farm button
        document.getElementById('add-farm').addEventListener('click', () => {
            this.openModal('farm');
        });
        
        // Submit Form button
        document.getElementById('submit-form').addEventListener('click', () => {
            this.submitForm();
        });
        
        // Close modals
        document.getElementById('close-success').addEventListener('click', () => {
            document.getElementById('success-modal').classList.add('hidden');
        });
        
        document.getElementById('close-error').addEventListener('click', () => {
            document.getElementById('error-modal').classList.add('hidden');
        });
    }

    initializeSectionControllers() {
        // Initialize section controllers with the renamed class
        new FarmSectionController(
            'manager-info',
            'toggle-manager-edit',
            'toggle-manager-visibility',
            false // Start expanded
        );
        
        new FarmSectionController(
            'team-members',
            null,
            'toggle-team-visibility',
            false // Start expanded
        );
    }

    initializeSampleData() {
        // Add one team member and one farm by default
        this.addTeamMemberRow();
        this.addFarmSection();
    }

    // Add new team member row
    addTeamMemberRow() {
        const teamMember = {
            id: Date.now().toString(),
            firstName: '',
            lastName: '',
            email: '',
            role: 'Laborer'
        };
        const row = this.createTeamMemberRow(teamMember);
        document.getElementById('team-members').appendChild(row);
        this.teamMembers.push(teamMember);
    }

    // Create team member row HTML
    createTeamMemberRow(teamMember) {
        const row = document.createElement('div');
        row.className = 'border border-gray-200 rounded-md p-4 mb-4';
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
        row.querySelector('.remove-team-member').addEventListener('click', () => {
            if (confirm('Are you sure you want to remove this team member?')) {
                row.remove();
                this.teamMembers = this.teamMembers.filter(member => member.id !== teamMember.id);
            }
        });

        // Add event listener for edit button
        row.querySelector('.edit-team-member').addEventListener('click', () => {
            this.openModal('team-member', teamMember);
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

        document.body.insertAdjacentHTML('beforeend', modalHTML);

        // Add event listeners
        const modal = document.getElementById('reusable-modal');
        const modalForm = document.getElementById('modal-form');
        const cancelBtn = document.getElementById('modal-cancel');

        cancelBtn.addEventListener('click', () => this.closeModal());
        modal.addEventListener('click', (e) => {
            if (e.target === modal) this.closeModal();
        });

        modalForm.addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleModalSave();
        });
    }

    openModal(type, data = null) {
        const modal = document.getElementById('reusable-modal');
        const modalTitle = document.getElementById('modal-title');
        const modalContent = document.getElementById('modal-content');

        this.currentModalType = type;
        this.currentModalData = data;

        // Set title and content based on type
        if (type === 'team-member') {
            modalTitle.textContent = data ? 'Edit Team Member' : 'Add Team Member';
            modalContent.innerHTML = this.getTeamMemberForm(data);
        } else if (type === 'farm') {
            modalTitle.textContent = data ? 'Edit Farm' : 'Add Farm';
            modalContent.innerHTML = this.getFarmForm(data);
            this.initializeFarmForm();
        }

        modal.classList.remove('hidden');
    }

    closeModal() {
        const modal = document.getElementById('reusable-modal');
        modal.classList.add('hidden');
        this.currentModalType = null;
        this.currentModalData = null;
    }

    getTeamMemberForm(data = null) {
        return `
            <div class="space-y-4">
                <div>
                    <label class="block text-sm font-medium text-gray-700">First Name</label>
                    <input type="text" name="firstName" class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                        value="${data ? data.firstName : ''}" required>
                </div>
                <div>
                    <label class="block text-sm font-medium text-gray-700">Last Name</label>
                    <input type="text" name="lastName" class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                        value="${data ? data.lastName : ''}" required>
                </div>
                <div>
                    <label class="block text-sm font-medium text-gray-700">Email</label>
                    <input type="email" name="email" class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                        value="${data ? data.email : ''}" required>
                </div>
                <div>
                    <label class="block text-sm font-medium text-gray-700">Role</label>
                    <select name="role" class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500">
                        ${this.getRoleOptions(data ? data.role : 'Laborer')}
                    </select>
                </div>
            </div>
        `;
    }

    getRoleOptions(selected) {
        const roles = ['Laborer', 'Farm Guide', 'Harvester', 'Irrigator', 'Planter', 'Weeder'];
        return roles.map(role => 
            `<option value="${role}" ${role === selected ? 'selected' : ''}>${role}</option>`
        ).join('');
    }

    getFarmForm(data = null) {
        return `
            <div class="space-y-4">
                <div>
                    <label class="block text-sm font-medium text-gray-700">Farm Name</label>
                    <input type="text" name="farmName" class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                        value="${data ? data.name : ''}" required>
                </div>
                <div>
                    <label class="block text-sm font-medium text-gray-700">Region</label>
                    <input type="text" name="region" class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                        value="${data ? data.region : 'Midwest'}" required>
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
        const fieldsContainer = document.getElementById('fields-container');
        const addFieldBtn = document.getElementById('add-field-btn');
        const fieldTemplate = document.getElementById('field-template');
        const markerTemplate = document.getElementById('marker-template');

        if (addFieldBtn) {
            addFieldBtn.addEventListener('click', () => {
                const fieldEntry = fieldTemplate.content.cloneNode(true);
                const field = fieldEntry.querySelector('.field-entry');
                
                // Add event listener for remove field button
                field.querySelector('.remove-field-btn').addEventListener('click', () => {
                    field.remove();
                });

                // Add event listener for add marker button
                field.querySelector('.add-marker-btn').addEventListener('click', () => {
                    const markerEntry = markerTemplate.content.cloneNode(true);
                    const marker = markerEntry.querySelector('.marker-entry');
                    
                    // Add event listeners for marker buttons
                    marker.querySelector('.get-location-btn').addEventListener('click', () => {
                        const latInput = marker.querySelector('[name="latitude"]');
                        const lngInput = marker.querySelector('[name="longitude"]');
                        this.getCurrentLocation(latInput, lngInput);
                    });

                    marker.querySelector('.remove-marker-btn').addEventListener('click', () => {
                        marker.remove();
                    });

                    field.querySelector('.markers-container').appendChild(marker);
                });

                fieldsContainer.appendChild(field);
            });
        }
    }

    handleModalSave() {
        const formData = new FormData(document.getElementById('modal-form'));
        const data = Object.fromEntries(formData.entries());

        if (this.currentModalType === 'team-member') {
            if (this.currentModalData) {
                // Update existing team member
                const member = this.teamMembers.find(m => m.id === this.currentModalData.id);
                if (member) {
                    Object.assign(member, {
                        firstName: data.firstName,
                        lastName: data.lastName,
                        email: data.email,
                        role: data.role
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
                    role: data.role
                };
                this.teamMembers.push(newMember);
                document.getElementById('team-members').appendChild(this.createTeamMemberRow(newMember));
            }
        } else if (this.currentModalType === 'farm') {
            // Gather field data
            const fields = [];
            document.querySelectorAll('.field-entry').forEach(fieldElem => {
                const fieldData = {
                    name: fieldElem.querySelector('[name="fieldName"]').value,
                    cropType: fieldElem.querySelector('[name="cropType"]').value,
                    boundaries: []
                };

                // Gather boundary markers
                fieldElem.querySelectorAll('.marker-entry').forEach(markerElem => {
                    fieldData.boundaries.push({
                        lat: markerElem.querySelector('[name="latitude"]').value,
                        lng: markerElem.querySelector('[name="longitude"]').value
                    });
                });

                fields.push(fieldData);
            });

            if (this.currentModalData) {
                // Update existing farm
                const farm = this.farms.find(f => f.id === this.currentModalData.id);
                if (farm) {
                    farm.name = data.farmName;
                    farm.region = data.region;
                    farm.fields = fields;
                    // Update the section in the UI
                    const section = document.querySelector(`[data-id="${farm.id}"]`);
                    if (section) {
                        section.replaceWith(this.createFarmSection(farm));
                    }
                }
            } else {
                // Add new farm
                const newFarm = {
                    id: Date.now().toString(),
                    name: data.farmName,
                    region: data.region,
                    fields: fields
                };
                this.farms.push(newFarm);
                document.getElementById('farms').appendChild(this.createFarmSection(newFarm));
            }
        }

        this.closeModal();
    }

    // Add new farm section
    addFarmSection() {
        const farm = {
            id: Date.now().toString(),
            name: '',
            region: 'Midwest', // Default to user's region
            fields: []
        };
        const section = this.createFarmSection(farm);
        document.getElementById('farms').appendChild(section);
        this.farms.push(farm);
    }

    // Create farm section HTML
    createFarmSection(farm) {
        const section = document.createElement('div');
        section.className = 'border border-gray-200 rounded-md p-4';
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
                <div>
                    <label class="block text-sm font-medium text-gray-700">Region</label>
                    <input type="text" class="farm-region mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500" required>
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
        section.querySelector('.farm-name').value = farm.name;
        section.querySelector('.farm-region').value = farm.region;
        
        // Add event listener for remove button
        section.querySelector('.remove-farm').addEventListener('click', () => {
            if (confirm('Are you sure you want to remove this farm and all its fields?')) {
                section.remove();
                this.farms = this.farms.filter(f => f.id !== farm.id);
            }
        });
        
        // Add field button
        section.querySelector('.add-field').addEventListener('click', () => {
            this.addField(section, farm);
        });
        
        // Add input change listeners
        const inputs = section.querySelectorAll('input');
        inputs.forEach(input => {
            input.addEventListener('change', (e) => {
                const currentFarm = this.farms.find(f => f.id === farm.id);
                if (currentFarm) {
                    if (e.target.classList.contains('farm-name')) currentFarm.name = e.target.value;
                    if (e.target.classList.contains('farm-region')) currentFarm.region = e.target.value;
                }
            });
        });
        
        return section;
    }

    // Add field to farm
    addField(farmSection, farm) {
        const field = {
            id: Date.now().toString(),
            name: '',
            boundaries: []
        };
        const fieldSection = this.createFieldSection(field, farmSection, farm);
        farmSection.querySelector('.fields').appendChild(fieldSection);
        farm.fields.push(field);
    }

    // Create field section HTML
    createFieldSection(field, farmSection, farm) {
        const section = document.createElement('div');
        section.className = 'border border-gray-200 rounded-md p-4';
        section.dataset.id = field.id;
        section.innerHTML = `
            <div class="mb-4">
                <div class="flex justify-between items-center">
                    <h4 class="font-medium text-gray-700">Field Details</h4>
                    <button class="remove-field bg-red-600 hover:bg-red-700 text-white px-3 py-1 rounded-md text-sm flex items-center">
                        <i class="fas fa-trash-alt mr-1"></i> Remove Field
                    </button>
                </div>
                <div class="mt-2">
                    <label class="block text-sm font-medium text-gray-700">Field Name</label>
                    <input type="text" class="field-name mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500" required>
                </div>
            </div>
            
            <div class="mb-4">
                <div class="flex justify-between items-center">
                    <h4 class="font-medium text-gray-700">Boundary Markers</h4>
                    <button class="add-boundary bg-green-600 hover:bg-green-700 text-white px-3 py-1 rounded-md text-sm flex items-center">
                        <i class="fas fa-plus mr-1"></i> Add Marker
                    </button>
                </div>
                <p class="text-xs text-gray-500 mt-1">Add at least 3 markers to define the field boundaries</p>
                
                <div class="boundary-markers mt-4 space-y-3">
                    <!-- Boundary marker rows will be added here -->
                </div>
            </div>
        `;
        
        // Set initial values
        section.querySelector('.field-name').value = field.name;
        
        // Add event listener for remove button
        section.querySelector('.remove-field').addEventListener('click', () => {
            if (confirm('Are you sure you want to remove this field and all its boundary markers?')) {
                section.remove();
                const currentFarm = this.farms.find(f => f.id === farm.id);
                if (currentFarm) {
                    currentFarm.fields = currentFarm.fields.filter(f => f.id !== field.id);
                }
            }
        });
        
        // Add boundary button
        section.querySelector('.add-boundary').addEventListener('click', () => {
            this.addBoundaryMarker(section, field);
        });
        
        // Add input change listeners
        section.querySelector('.field-name').addEventListener('change', (e) => {
            const currentFarm = this.farms.find(f => f.id === farm.id);
            if (currentFarm) {
                const currentField = currentFarm.fields.find(f => f.id === field.id);
                if (currentField) {
                    currentField.name = e.target.value;
                }
            }
        });
        
        return section;
    }

    // Add boundary marker to field
    addBoundaryMarker(fieldSection, field) {
        const marker = {
            id: Date.now().toString(),
            lat: '',
            lng: ''
        };
        const markerRow = this.createBoundaryMarkerRow(marker, fieldSection, field);
        fieldSection.querySelector('.boundary-markers').appendChild(markerRow);
        field.boundaries.push(marker);
    }

    // Create boundary marker row HTML
    createBoundaryMarkerRow(marker, fieldSection, field) {
        const row = document.createElement('div');
        row.className = 'grid grid-cols-1 md:grid-cols-3 gap-3 items-end';
        row.dataset.id = marker.id;
        row.innerHTML = `
            <div>
                <label class="block text-sm font-medium text-gray-700">Latitude</label>
                <input type="number" step="any" class="marker-lat mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500" placeholder="e.g. 40.7128" required>
            </div>
            <div>
                <label class="block text-sm font-medium text-gray-700">Longitude</label>
                <input type="number" step="any" class="marker-lng mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500" placeholder="e.g. -74.0060" required>
            </div>
            <div class="flex space-x-2">
                <button class="get-location bg-blue-600 hover:bg-blue-700 text-white px-3 py-1 rounded-md text-sm flex items-center">
                    <i class="fas fa-location-arrow mr-1"></i> Current
                </button>
                <button class="remove-marker bg-red-600 hover:bg-red-700 text-white px-3 py-1 rounded-md text-sm flex items-center">
                    <i class="fas fa-trash-alt mr-1"></i>
                </button>
            </div>
        `;
        
        // Set initial values
        row.querySelector('.marker-lat').value = marker.lat;
        row.querySelector('.marker-lng').value = marker.lng;
        
        // Add event listener for remove button
        row.querySelector('.remove-marker').addEventListener('click', () => {
            if (confirm('Are you sure you want to remove this boundary marker?')) {
                row.remove();
                field.boundaries = field.boundaries.filter(m => m.id !== marker.id);
            }
        });
        
        // Add event listener for current location button
        row.querySelector('.get-location').addEventListener('click', () => {
            this.getCurrentLocation(
                row.querySelector('.marker-lat'),
                row.querySelector('.marker-lng'),
                marker
            );
        });
        
        // Add input change listeners
        const inputs = row.querySelectorAll('input');
        inputs.forEach(input => {
            input.addEventListener('change', (e) => {
                const currentMarker = field.boundaries.find(m => m.id === marker.id);
                if (currentMarker) {
                    if (e.target.classList.contains('marker-lat')) currentMarker.lat = e.target.value;
                    if (e.target.classList.contains('marker-lng')) currentMarker.lng = e.target.value;
                }
            });
        });
        
        return row;
    }

    // Get current location
    getCurrentLocation(latInput, lngInput, marker) {
        if (navigator.geolocation) {
            latInput.disabled = true;
            lngInput.disabled = true;
            
            // Show loading state
            const button = latInput.parentElement.parentElement.querySelector('.get-location');
            const originalHTML = button.innerHTML;
            button.innerHTML = '<i class="fas fa-spinner fa-spin mr-1"></i> Locating...';
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
                    console.error('Error getting location:', error);
                    alert('Could not get your current location. Please enter coordinates manually.');
                    
                    // Restore button
                    button.innerHTML = originalHTML;
                    button.disabled = false;
                    latInput.disabled = false;
                    lngInput.disabled = false;
                }
            );
        } else {
            alert('Geolocation is not supported by your browser. Please enter coordinates manually.');
        }
    }

    // Validate form data
    validateForm() {
        let isValid = true;
        const errors = [];
        
        // Validate team members
        if (this.teamMembers.length === 0) {
            errors.push('Please add at least one team member');
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
            errors.push('Please add at least one farm');
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
                            errors.push(`Field ${fieldIndex + 1} in farm "${farm.name}" is missing a name`);
                            isValid = false;
                        }
                        
                        // Validate boundary markers
                        if (field.boundaries.length < 3) {
                            errors.push(`Field "${field.name}" in farm "${farm.name}" needs at least 3 boundary markers`);
                            isValid = false;
                        } else {
                            field.boundaries.forEach((marker, markerIndex) => {
                                if (!marker.lat || !marker.lng) {
                                    errors.push(`Boundary marker ${markerIndex + 1} in field "${field.name}" is missing coordinates`);
                                    isValid = false;
                                }
                            });
                        }
                    });
                }
            });
        }
        
        if (!isValid) {
            this.showError('Validation Error', errors.join('<br>'));
        }
        
        return isValid;
    }

    // Show error message
    showError(title, message) {
        document.getElementById('error-title').textContent = title;
        document.getElementById('error-message').innerHTML = message;
        document.getElementById('error-modal').classList.remove('hidden');
    }

    // Submit form data
    async submitForm() {
        if (!this.validateForm()) {
            return;
        }
        
        // Get CSRF token
        const csrfToken = document.querySelector('input[name="csrf_token"]').value;
        
        // Prepare form data
        const formData = {
            manager: {
                firstName: document.getElementById('first_name').value,
                lastName: document.getElementById('last_name').value,
                email: document.getElementById('email').value
            },
            teamMembers: this.teamMembers,
            farms: this.farms
        };
        
        // Show loading state on submit button
        const submitButton = document.getElementById('submit-form');
        const originalHTML = submitButton.innerHTML;
        submitButton.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i> Processing...';
        submitButton.disabled = true;
        
        try {
            const response = await fetch('/farm/register_farm', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify(formData),
                credentials: 'same-origin'
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Registration failed');
            }

            const data = await response.json();
            if (data.success) {
                document.getElementById('success-modal').classList.remove('hidden');
                // Redirect to dashboard after a delay
                setTimeout(() => {
                    window.location.href = '/farm/dashboard';
                }, 2000);
            } else {
                throw new Error(data.error || 'Registration failed');
            }
        } catch (error) {
            console.error('Error:', error);
            this.showError('Submission Failed', error.message || 'There was an error submitting your farm registration. Please try again.');
        } finally {
            // Restore button
            submitButton.innerHTML = originalHTML;
            submitButton.disabled = false;
        }
    }
}

// Initialize the controller when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    const controller = new FarmRegistrationController();
});