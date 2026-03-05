const container = document.getElementById('tierlist-container');
const saveIndicator = document.getElementById('save-indicator');
const tooltip = document.getElementById('tooltip');
const zoomDefaultBtn = document.getElementById('zoom-default');

let currentZoom = 35;
let defaultZoom = 35;
let activeYearMode = null; // 'first' or 'rerank'
let currentColumns = 17;

const zoomValue = document.getElementById('zoom-value');
const zoomOutBtn = document.getElementById('zoom-out');
const zoomInBtn = document.getElementById('zoom-in');
const toggleYearFirstBtn = document.getElementById('toggle-year-first');
const toggleYearRerankBtn = document.getElementById('toggle-year-rerank');

function applyZoom() {
    zoomValue.textContent = currentZoom + '%';
    container.style.zoom = currentZoom / 100;
}

function updateTooltipPosition(e) {
    const tooltipWidth = tooltip.offsetWidth;
    const pageWidth = window.innerWidth;
    let xPos = e.pageX + 15;

    // If tooltip would go off-screen to the right, flip it to the left of the cursor
    if (xPos + tooltipWidth > pageWidth - 15) {
        xPos = e.pageX - tooltipWidth - 15;
    }

    tooltip.style.left = xPos + 'px';
    tooltip.style.top = (e.pageY + 15) + 'px';
}

zoomDefaultBtn.addEventListener('click', () => {
    currentZoom = defaultZoom;
    applyZoom();
});

zoomOutBtn.addEventListener('click', () => {
    if (currentZoom > 5) {
        currentZoom = Math.ceil(currentZoom / 5) * 5 - 5;
        if (currentZoom < 5) currentZoom = 5;
        applyZoom();
    }
});

zoomInBtn.addEventListener('click', () => {
    if (currentZoom < 200) {
        currentZoom = Math.floor(currentZoom / 5) * 5 + 5;
        if (currentZoom > 200) currentZoom = 200;
        applyZoom();
    }
});

toggleYearFirstBtn.addEventListener('click', () => {
    if (activeYearMode === 'first') {
        activeYearMode = null;
        toggleYearFirstBtn.classList.remove('active');
    } else {
        activeYearMode = 'first';
        toggleYearFirstBtn.classList.add('active');
        toggleYearRerankBtn.classList.remove('active');
    }
    render(currentColumns);
});

toggleYearRerankBtn.addEventListener('click', () => {
    if (activeYearMode === 'rerank') {
        activeYearMode = null;
        toggleYearRerankBtn.classList.remove('active');
    } else {
        activeYearMode = 'rerank';
        toggleYearRerankBtn.classList.add('active');
        toggleYearFirstBtn.classList.remove('active');
    }
    render(currentColumns);
});

// Toggle Hover Global Tooltip
[
    { el: toggleYearFirstBtn, text: "Year First Visited" },
    { el: toggleYearRerankBtn, text: "Year Re-ranked" }
].forEach(item => {
    item.el.addEventListener('mouseenter', () => {
        tooltip.textContent = item.text;
        tooltip.style.opacity = '1';
    });
    item.el.addEventListener('mousemove', e => {
        updateTooltipPosition(e);
    });
    item.el.addEventListener('mouseleave', () => {
        tooltip.style.opacity = '0';
    });
});

// Run Tierlist Button Logic
const runTierlistBtn = document.getElementById('run-tierlist-btn');
runTierlistBtn.addEventListener('click', async () => {
    runTierlistBtn.textContent = 'Running...';
    runTierlistBtn.disabled = true;
    runTierlistBtn.style.opacity = '0.7';

    try {
        const res = await fetch('/api/run_tierlist', { method: 'POST' });
        const data = await res.json().catch(() => ({ error: "Failed to parse server response" }));

        if (res.ok) {
            saveIndicator.textContent = 'Successfully generated images!';
            saveIndicator.className = 'save-indicator saved';
            setTimeout(() => {
                saveIndicator.style.display = "";
                saveIndicator.className = "save-indicator";
            }, 3000);
        } else {
            const details = data.details ? `: ${data.details}` : (data.error ? `: ${data.error}` : '');
            saveIndicator.textContent = 'Error' + details;
            saveIndicator.className = 'save-indicator error';
        }
    } catch (err) {
        saveIndicator.textContent = 'Error running script: ' + err.message;
        saveIndicator.className = 'save-indicator error';
    } finally {
        runTierlistBtn.textContent = 'Export imgs';
        runTierlistBtn.disabled = false;
        runTierlistBtn.style.opacity = '1';

        // Ensure indicator fades out even on error after a bit longer
        if (saveIndicator.classList.contains('error')) {
            setTimeout(() => {
                if (saveIndicator.classList.contains('error')) {
                    saveIndicator.style.display = "";
                    saveIndicator.className = "save-indicator";
                }
            }, 5000);
        }
    }
});

let globalTierDict = {};
let unassignedLogos = []; // list of logo paths
const imageCache = new Map();

// DOM elements for Modal and Dropdown
const unassignedBtn = document.getElementById('unassigned-btn');
const unassignedDropdown = document.getElementById('unassigned-dropdown');
const unassignedBadge = document.getElementById('unassigned-badge');

const editModal = document.getElementById('edit-modal');
const modalImg = document.getElementById('modal-img');
const editForm = document.getElementById('edit-form');
const btnCancel = document.getElementById('btn-cancel');

unassignedBtn.addEventListener('click', () => {
    unassignedDropdown.classList.toggle('show');
});

// Close dropdown when clicking outside
document.addEventListener('click', (e) => {
    if (!unassignedBtn.contains(e.target) && !unassignedDropdown.contains(e.target)) {
        unassignedDropdown.classList.remove('show');
    }
});

// Close modal when clicking outside
editModal.addEventListener('click', (e) => {
    if (e.target === editModal) {
        btnCancel.click();
    }
});

btnCancel.addEventListener('click', () => {
    editModal.classList.remove('active');
    setTimeout(() => {
        if (!editModal.classList.contains('active')) {
            editModal.style.display = 'none';
        }
    }, 300);
});

const navPrevBtn = document.getElementById('nav-prev');
const navNextBtn = document.getElementById('nav-next');
let _allOrdered = [];
let _currentIndex = -1;

function getOrderedRestaurants() {
    const list = [];
    ['S', 'A', 'B', 'C', 'D', 'E', 'F'].forEach(tier => {
        const tierItems = globalTierDict[tier];
        if (tierItems) {
            Object.entries(tierItems).forEach(([name, info]) => {
                list.push({ name, tier, info });
            });
        }
    });
    return list;
}

function updateNavButtons(currentName) {
    _allOrdered = getOrderedRestaurants();
    _currentIndex = _allOrdered.findIndex(r => r.name === currentName);

    if (_currentIndex > 0) {
        navPrevBtn.style.display = 'flex';
    } else {
        navPrevBtn.style.display = 'none';
    }

    if (_currentIndex >= 0 && _currentIndex < _allOrdered.length - 1) {
        navNextBtn.style.display = 'flex';
    } else {
        navNextBtn.style.display = 'none';
    }
}

async function navigateModal(direction) {
    const nextIdx = _currentIndex + direction;
    if (nextIdx >= 0 && nextIdx < _allOrdered.length) {
        const nextItem = _allOrdered[nextIdx];
        openEditModal(nextItem.name, nextItem.tier, nextItem.info);
    }
}

navPrevBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    navigateModal(-1);
});

navNextBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    navigateModal(1);
});

// Close modal on Esc key and navigate with Arrows
window.addEventListener('keydown', (e) => {
    if (editModal.classList.contains('active')) {
        if (e.key === 'Escape') {
            btnCancel.click();
        } else if (['ArrowLeft', 'ArrowRight'].includes(e.key)) {
            // Don't navigate if typing in input/textarea
            if (['INPUT', 'TEXTAREA'].includes(document.activeElement.tagName)) return;

            if (e.key === 'ArrowLeft' && _currentIndex > 0) {
                navigateModal(-1);
            } else if (e.key === 'ArrowRight' && _currentIndex < _allOrdered.length - 1) {
                navigateModal(1);
            }
        }
    }
});

async function init() {
    try {
        // Fetch logos and dict in parallel
        const [dataRes, logosRes] = await Promise.all([
            fetch('/api/data'),
            fetch('/api/logos')
        ]);

        if (!dataRes.ok || !logosRes.ok) throw new Error('Failed to fetch from server');

        const [data, logosData] = await Promise.all([
            dataRes.json(),
            logosRes.json()
        ]);

        globalTierDict = data.tier_dict;
        const columns = data.num_logos_per_row || 17;

        // Determine unassigned logos
        const allExtractedLogos = new Set();
        Object.values(globalTierDict).forEach(tierObj => {
            Object.values(tierObj).forEach(info => {
                allExtractedLogos.add(info.path_to_logo_image.toLowerCase());
            });
        });

        unassignedLogos = logosData.logos.filter(l => !allExtractedLogos.has(`logos/${l}`.toLowerCase()));
        updateUnassignedDropdown();

        // Collect ALL image paths
        const imagePaths = [];

        Object.values(globalTierDict).forEach(tierObj => {
            Object.values(tierObj).forEach(info => {
                imagePaths.push(info.path_to_logo_image);
                if (info.price) imagePaths.push(`assets/png/${info.price}.png`);
                if (info.vegan) imagePaths.push(`assets/png/Vegan.png`);
                if (info.year) {
                    imagePaths.push(`assets/png/${info.year}.png`);
                    imagePaths.push(`assets/png/${info.year}_highlighted.png`);
                }
                if (info.year_first_visited) imagePaths.push(`assets/png/${info.year_first_visited}.png`);
            });
        });

        // Preload everything before render
        await loadImagesWithProgress(imagePaths);

        // Fade out loading overlay
        const overlay = document.getElementById('loading-overlay');
        overlay.classList.add('fade-out');

        // Dynamic Zoom Calculation
        const tierRowWidth = 200 + 40 + (columns * 210); // label + gaps + content
        const availableWidth = window.innerWidth - 40; // some margin
        currentZoom = Math.min(100, Math.floor((availableWidth / tierRowWidth) * 100) - 1);
        if (currentZoom < 10) currentZoom = 10;
        defaultZoom = currentZoom;
        applyZoom();

        currentColumns = columns;
        render(columns);
    } catch (err) {
        container.innerHTML = `
        <div class="error">
            <h2>Error!</h2>
            <p>${err.message}</p>
            <p>Make sure editor_server.py is running on port 8000.</p>
        </div>`;
    }
}

function updateUnassignedDropdown() {
    unassignedBadge.textContent = unassignedLogos.length;
    unassignedDropdown.innerHTML = '';

    if (unassignedLogos.length === 0) {
        const empty = document.createElement('div');
        empty.className = 'dropdown-item';
        empty.textContent = 'None';
        empty.style.color = '#888';
        empty.style.cursor = 'default';
        unassignedDropdown.appendChild(empty);
        return;
    }

    unassignedLogos.forEach(logo => {
        const item = document.createElement('div');
        item.className = 'dropdown-item';
        item.textContent = logo.replace(/\.[^/.]+$/, ""); // remove extension for display
        item.addEventListener('click', () => {
            unassignedDropdown.classList.remove('show');
            openCreateModal(logo);
        });
        unassignedDropdown.appendChild(item);
    });
}

function render(columns) {
    container.innerHTML = '';
    const tiers = ['S', 'A', 'B', 'C', 'D', 'E', 'F'];

    tiers.forEach(tier => {
        const row = document.createElement('div');
        row.className = 'tier-row';

        const label = document.createElement('div');
        label.className = 'tier-label';
        label.dataset.tier = tier;
        label.textContent = tier;

        const content = document.createElement('div');
        content.className = 'tier-content';
        content.dataset.tier = tier;
        content.style.setProperty('--columns', columns);

        const restaurants = globalTierDict[tier];
        if (restaurants) {
            Object.keys(restaurants).forEach(name => {
                const info = restaurants[name];

                const wrapper = document.createElement('div');
                wrapper.className = 'logo-item-wrapper';
                wrapper.dataset.name = name;
                wrapper.dataset.tier = tier;
                wrapper.draggable = true;

                const img = imageCache.get(info.path_to_logo_image);

                img.classList.add('logo-item');
                img.alt = name;

                wrapper.appendChild(img);

                if (info.price) {
                    const pricePath = `assets/png/${info.price}.png`;
                    const basePriceImg = imageCache.get(pricePath);

                    if (basePriceImg) {
                        const priceImg = basePriceImg.cloneNode();
                        priceImg.className = 'price-tag';
                        wrapper.appendChild(priceImg);
                    }
                }

                if (info.vegan) {
                    const veganPath = `assets/png/Vegan.png`;
                    const baseVeganImg = imageCache.get(veganPath);

                    if (baseVeganImg) {
                        const veganImg = baseVeganImg.cloneNode();
                        veganImg.className = 'vegan-tag';
                        wrapper.appendChild(veganImg);
                    }
                }

                if (activeYearMode) {
                    let yearToDisplay = activeYearMode === 'first' ? info.year_first_visited : info.year;
                    if (yearToDisplay) {
                        let suffix = "";
                        const isForced = info.highlighted === "true" || info.highlighted === true;
                        if (activeYearMode === 'rerank' && (info.year !== info.year_first_visited || isForced)) {
                            suffix = "_highlighted";
                        }
                        const yearPath = `assets/png/${yearToDisplay}${suffix}.png`;
                        const baseYearImg = imageCache.get(yearPath);
                        if (baseYearImg) {
                            const yearImg = baseYearImg.cloneNode();
                            yearImg.className = 'year-tag';
                            wrapper.appendChild(yearImg);
                        }
                    }
                }

                // Tooltip
                wrapper.addEventListener('mouseenter', e => {
                    tooltip.textContent = name;
                    tooltip.style.opacity = '1';
                });

                wrapper.addEventListener('mousemove', e => {
                    updateTooltipPosition(e);
                });

                wrapper.addEventListener('mouseleave', e => {
                    tooltip.style.opacity = '0';
                });

                // Drag events
                wrapper.addEventListener('dragstart', handleDragStart);
                wrapper.addEventListener('dragend', handleDragEnd);

                // Double Click to Edit
                wrapper.addEventListener('dblclick', function () {
                    const curName = this.dataset.name;
                    const curTier = this.dataset.tier;
                    const curInfo = globalTierDict[curTier][curName];
                    openEditModal(curName, curTier, curInfo);
                });

                content.appendChild(wrapper);
            });
        }

        content.addEventListener('dragover', handleDragOver);
        content.addEventListener('dragleave', handleDragLeave);
        content.addEventListener('drop', handleDrop);

        row.appendChild(label);
        row.appendChild(content);
        container.appendChild(row);
    });
}

let draggedElement = null;

function handleDragStart(e) {
    draggedElement = this;
    this.classList.add('dragging');
    e.dataTransfer.effectAllowed = 'move';
    e.dataTransfer.setData('text/plain', this.dataset.name);
    tooltip.style.opacity = '0';
}

function handleDragEnd(e) {
    this.classList.remove('dragging');
    draggedElement = null;
    document.querySelectorAll('.drag-over').forEach(el => el.classList.remove('drag-over'));
}

function handleDragOver(e) {
    if (e.preventDefault) e.preventDefault();
    e.dataTransfer.dropEffect = 'move';

    this.classList.add('drag-over');

    const afterElement = getDragAfterElement(this, e.clientX, e.clientY);
    if (afterElement == null) {
        this.appendChild(draggedElement);
    } else {
        if (draggedElement !== afterElement) {
            this.insertBefore(draggedElement, afterElement);
        }
    }
    return false;
}

function getDragAfterElement(container, x, y) {
    const draggableElements = [...container.querySelectorAll('.logo-item-wrapper:not(.dragging)')];

    for (const child of draggableElements) {
        const box = child.getBoundingClientRect();

        // Cursor is completely above this element's row
        if (y < box.top - 10) {
            return child;
        }

        // Cursor is on this element's row
        if (y >= box.top - 10 && y <= box.bottom + 10) {
            if (x < box.left + box.width / 2) {
                return child;
            }
        }
    }
    return null;
}

function handleDragLeave(e) {
    if (!this.contains(e.relatedTarget)) {
        this.classList.remove('drag-over');
    }
}

function rebuildTierDict() {
    const updatedDict = {};
    const draggedName = draggedElement ? draggedElement.dataset.name : null;

    ['S', 'A', 'B', 'C', 'D', 'E', 'F'].forEach(tier => {
        updatedDict[tier] = {};
        const tierContainer = document.querySelector(`.tier-content[data-tier="${tier}"]`);
        if (tierContainer) {
            const items = tierContainer.querySelectorAll('.logo-item-wrapper');
            items.forEach(item => {
                const name = item.dataset.name;
                const oldTier = item.getAttribute('data-tier');

                // update the tier data on the DOM element too
                item.dataset.tier = tier;
                item.setAttribute('data-tier', tier);

                let info = null;
                for (let t of ['S', 'A', 'B', 'C', 'D', 'E', 'F']) {
                    if (globalTierDict[t] && globalTierDict[t][name]) {
                        info = globalTierDict[t][name];
                        break;
                    }
                }

                if (info) {
                    // Use name comparison as it's more stable
                    if (name === draggedName && oldTier && oldTier !== tier) {
                        const currentYear = new Date().getFullYear();
                        console.log(`[TierChange] ${name} moved from ${oldTier} to ${tier}. Updating year to ${currentYear}`);
                        if (info.year !== currentYear) {
                            info.year = currentYear;
                        }
                    }
                    updatedDict[tier][name] = info;
                }
            });
        }
    });
    globalTierDict = updatedDict;
}

async function handleDrop(e) {
    if (e.stopPropagation) e.stopPropagation();
    this.classList.remove('drag-over');

    if (draggedElement) {
        rebuildTierDict();
        await saveToServer();
        render(currentColumns);
    }
    return false;
}

async function saveToServer() {
    saveIndicator.textContent = "Saving...";
    saveIndicator.className = "save-indicator saving";

    try {
        const res = await fetch('/api/update', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(globalTierDict)
        });

        if (res.ok) {
            saveIndicator.textContent = "Saved!";
            saveIndicator.className = "save-indicator saved";
            setTimeout(() => {
                saveIndicator.style.display = "";
                saveIndicator.className = "save-indicator";
            }, 2000);
        } else {
            throw new Error("Bad response");
        }
    } catch (err) {
        saveIndicator.textContent = "Error saving!";
        saveIndicator.className = "save-indicator error";
    }
}

// Progress bar
function loadImagesWithProgress(paths) {
    return new Promise(resolve => {
        const progressFill = document.getElementById('progress-fill');
        const progressText = document.getElementById('progress-text');

        const unique = [...new Set(paths)];
        let loaded = 0;
        const total = unique.length;

        if (total === 0) {
            resolve();
            return;
        }

        unique.forEach(path => {
            const img = new Image();

            img.onload = async () => {
                try {
                    if (img.decode) await img.decode();
                } catch (e) {
                    console.warn("Decoding failed for", path, e);
                }
                imageCache.set(path, img);

                loaded++;
                const percent = Math.round((loaded / total) * 100);
                if (progressFill) progressFill.style.width = percent + '%';
                if (progressText) progressText.textContent = percent + '%';

                if (loaded === total) {
                    resolve();
                }
            };

            img.onerror = () => {
                console.error("Failed to load image:", path);
                loaded++;
                const percent = Math.round((loaded / total) * 100);
                if (progressFill) progressFill.style.width = percent + '%';
                if (progressText) progressText.textContent = percent + '%';

                if (loaded === total) {
                    resolve();
                }
            };

            img.src = path;
        });
    });
}

async function ensureImageInCache(path) {
    if (imageCache.has(path)) return imageCache.get(path);
    return new Promise((resolve) => {
        const img = new Image();
        img.onload = () => {
            imageCache.set(path, img);
            resolve(img);
        };
        img.onerror = () => {
            console.warn("Failed to catch-load image:", path);
            // Return a dummy small transparent pixel or similar to avoid crash
            const dummy = new Image();
            imageCache.set(path, dummy);
            resolve(dummy);
        };
        img.src = path;
    });
}

// Modal Logic
const editName = document.getElementById('edit-name');
const editTier = document.getElementById('edit-tier');
const editPrice = document.getElementById('edit-price');
const editYear = document.getElementById('edit-year');
const editYearFirst = document.getElementById('edit-year-first');
const editAddress = document.getElementById('edit-address');
const editDescription = document.getElementById('edit-description');
const editVegan = document.getElementById('edit-vegan');
const editHighlighted = document.getElementById('edit-highlighted');

const editOriginalName = document.getElementById('edit-original-name');
const editMode = document.getElementById('edit-mode');
const editLogoPath = document.getElementById('edit-logo-path');
const modalTitle = document.getElementById('modal-title');

const btnSave = document.getElementById('btn-save');
let initialFormState = "";

function checkFormChanged() {
    const currentState = getFormState();
    const hasChanged = currentState !== initialFormState;

    // Filename character validation
    const invalidChars = /[<>:"/\\|?*]/;
    const isNameInvalid = invalidChars.test(editName.value);

    if (isNameInvalid) {
        editName.classList.add('invalid-input');
        editName.setCustomValidity("Invalid characters for filename");
    } else {
        editName.classList.remove('invalid-input');
        editName.setCustomValidity("");
    }

    // Year validation
    const yearVal = parseInt(editYear.value);
    const yearFirstVal = parseInt(editYearFirst.value);
    const isYearInvalid = isNaN(yearVal) || !Number.isInteger(Number(editYear.value));
    const isYearFirstInvalid = isNaN(yearFirstVal) || !Number.isInteger(Number(editYearFirst.value));
    const isYearOrderInvalid = yearFirstVal > yearVal;

    if (isYearInvalid) {
        editYear.classList.add('invalid-input');
        editYear.setCustomValidity("Must be a valid integer year");
    } else {
        editYear.classList.remove('invalid-input');
        editYear.setCustomValidity("");
    }

    if (isYearFirstInvalid || isYearOrderInvalid) {
        editYearFirst.classList.add('invalid-input');
        if (isYearFirstInvalid) {
            editYearFirst.setCustomValidity("Must be a valid integer year");
        } else {
            editYearFirst.setCustomValidity("First visit cannot be after re-ranked year");
        }
    } else {
        editYearFirst.classList.remove('invalid-input');
        editYearFirst.setCustomValidity("");
    }

    const isValid = editForm.checkValidity();
    btnSave.disabled = !hasChanged || !isValid || isNameInvalid || isYearInvalid || isYearFirstInvalid || isYearOrderInvalid;
}

function getFormState() {
    return JSON.stringify({
        name: editName.value.trim(),
        tier: editTier.value,
        price: editPrice.value,
        year: editYear.value,
        yearFirst: editYearFirst.value,
        address: editAddress.value.trim(),
        description: editDescription.value.trim(),
        vegan: editVegan.checked,
        highlighted: editHighlighted.checked
    });
}

// Attach change listeners to all form inputs
[editName, editTier, editPrice, editYear, editYearFirst, editAddress, editDescription, editVegan, editHighlighted].forEach(el => {
    el.addEventListener('input', checkFormChanged);
    el.addEventListener('change', checkFormChanged);
});

function openEditModal(name, tier, info) {
    editName.classList.remove('invalid-input');
    editName.setCustomValidity("");

    editMode.value = 'edit';
    modalTitle.textContent = 'Edit Metadata';
    modalImg.src = info.path_to_logo_image;
    editLogoPath.value = info.path_to_logo_image;
    editOriginalName.value = name;
    document.getElementById('edit-original-tier').value = tier;
    document.getElementById('edit-original-price').value = info.price || '1';

    editName.value = name;
    editTier.value = tier;
    editPrice.value = info.price || '1';
    editYear.value = info.year || new Date().getFullYear();
    editYearFirst.value = info.year_first_visited || new Date().getFullYear();
    editAddress.value = info.address || '';
    editDescription.value = info.description || '';
    editVegan.checked = !!info.vegan;
    editHighlighted.checked = info.highlighted === "true" || info.highlighted === true;

    initialFormState = getFormState();
    btnSave.disabled = true;

    updateNavButtons(name);
    showModal();
}

function openCreateModal(logoFilename) {
    editName.classList.remove('invalid-input');
    editName.setCustomValidity("");

    editMode.value = 'create';
    modalTitle.textContent = 'Add New Restaurant';
    const path = 'logos/' + logoFilename;
    modalImg.src = path;
    editLogoPath.value = path;
    ensureImageInCache(path); // Ensure it's in cache for saving later

    const guessedName = logoFilename.replace(/\.[^/.]+$/, "");
    editOriginalName.value = '';

    editName.value = guessedName;
    editTier.value = 'S';
    editPrice.value = '1';
    editYear.value = new Date().getFullYear();
    editYearFirst.value = new Date().getFullYear();
    editAddress.value = '';
    editDescription.value = '';
    editVegan.checked = false;
    editHighlighted.checked = false;

    initialFormState = getFormState();
    btnSave.disabled = true;

    navPrevBtn.style.display = 'none';
    navNextBtn.style.display = 'none';
    showModal();
}

function showModal() {
    editModal.style.display = 'flex';
    // Force reflow
    editModal.offsetHeight;
    editModal.classList.add('active');
}

editForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const mode = editMode.value;
    const origName = editOriginalName.value;

    const name = editName.value.trim();
    const tier = editTier.value;
    const price = editPrice.value ? parseInt(editPrice.value) : null;

    let newInfo = {};
    if (mode === 'edit') {
        for (let t of ['S', 'A', 'B', 'C', 'D', 'E', 'F']) {
            if (globalTierDict[t] && globalTierDict[t][origName]) {
                newInfo = { ...globalTierDict[t][origName] };
                // Delay deletion until we know if it's a move or in-place update
                break;
            }
        }
    }

    newInfo.path_to_logo_image = editLogoPath.value;
    if (price) {
        newInfo.price = price;
    } else {
        delete newInfo.price;
    }
    if (editYear.value) {
        newInfo.year = parseInt(editYear.value);
    } else {
        delete newInfo.year;
    }
    if (editYearFirst.value) {
        newInfo.year_first_visited = parseInt(editYearFirst.value);
    } else {
        delete newInfo.year_first_visited;
    }
    if (editAddress.value.trim()) {
        newInfo.address = editAddress.value.trim();
    } else {
        delete newInfo.address;
    }
    if (editDescription.value.trim()) {
        newInfo.description = editDescription.value.trim();
    } else {
        delete newInfo.description;
    }
    if (editVegan.checked) {
        newInfo.vegan = true;
    } else {
        delete newInfo.vegan;
    }

    if (editHighlighted.checked) {
        newInfo.highlighted = "true";
    } else {
        delete newInfo.highlighted;
    }

    if (mode === 'edit') {
        const oldPath = editLogoPath.value;
        const ext = oldPath.split('.').pop();
        const newPath = `logos/${name}.${ext}`;
        if (oldPath !== newPath) {
            newInfo.path_to_logo_image = newPath;
            try {
                await fetch('/api/rename_logo', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ old_path: oldPath, new_path: newPath })
                });
                await ensureImageInCache(newPath);
            } catch (e) {
                console.error("Failed to rename logo file", e);
            }
        }
    } else if (mode === 'create') {
        unassignedLogos = unassignedLogos.filter(l => `logos/${l}` !== editLogoPath.value);
        updateUnassignedDropdown();

        const oldPath = editLogoPath.value;
        const ext = oldPath.split('.').pop();
        const newPath = `logos/${name}.${ext}`;

        if (oldPath !== newPath) {
            newInfo.path_to_logo_image = newPath;
            try {
                await fetch('/api/rename_logo', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ old_path: oldPath, new_path: newPath })
                });
                await ensureImageInCache(newPath);
            } catch (e) {
                console.error("Failed to rename logo file", e);
            }
        } else {
            await ensureImageInCache(oldPath);
        }
    }

    // Insert into correct tier, keeping position if tier/price didn't change
    if (!globalTierDict[tier]) globalTierDict[tier] = {};

    const origTier = document.getElementById('edit-original-tier').value;
    const origPrice = document.getElementById('edit-original-price').value ? parseInt(document.getElementById('edit-original-price').value) : null;

    const tierChanged = tier !== origTier;
    const priceChanged = price !== origPrice;

    if (mode === 'edit' && !tierChanged && !priceChanged) {
        // REPLACE IN PLACE
        const updatedTierItems = {};
        for (const [k, v] of Object.entries(globalTierDict[tier])) {
            if (k === origName) {
                updatedTierItems[name] = newInfo;
            } else {
                updatedTierItems[k] = v;
            }
        }
        globalTierDict[tier] = updatedTierItems;
    } else {
        // MOVE/SORT (Price or Tier changed, or it's a new entry)

        // If editing and moving, delete the old entry now
        if (mode === 'edit') {
            delete globalTierDict[origTier][origName];
        }

        const newTierItems = {};
        let inserted = false;
        const pVal = price || 0;

        for (const [k, v] of Object.entries(globalTierDict[tier])) {
            const itemP = v.price || 0;
            if (!inserted && itemP > pVal) {
                newTierItems[name] = newInfo;
                inserted = true;
            }
            newTierItems[k] = v;
        }
        if (!inserted) {
            newTierItems[name] = newInfo;
        }
        globalTierDict[tier] = newTierItems;
    }

    editModal.classList.remove('active');
    setTimeout(() => {
        if (!editModal.classList.contains('active')) {
            editModal.style.display = 'none';
        }
    }, 300);

    // Rebuild or update DOM directly
    let wrapper = null;
    if (mode === 'edit') {
        wrapper = document.querySelector(`.logo-item-wrapper[data-name="${origName}"]`);
    }

    if (!wrapper) {
        // creating new
        wrapper = document.createElement('div');
        wrapper.className = 'logo-item-wrapper';
        wrapper.draggable = true;

        // attach events
        wrapper.addEventListener('mouseenter', e => {
            tooltip.textContent = wrapper.dataset.name;
            tooltip.style.opacity = '1';
        });
        wrapper.addEventListener('mousemove', e => {
            updateTooltipPosition(e);
        });
        wrapper.addEventListener('mouseleave', e => {
            tooltip.style.opacity = '0';
        });
        wrapper.addEventListener('dragstart', handleDragStart);
        wrapper.addEventListener('dragend', handleDragEnd);
        wrapper.addEventListener('dblclick', function () {
            const curName = this.dataset.name;
            const curTier = this.dataset.tier;
            const curInfo = globalTierDict[curTier][curName];
            openEditModal(curName, curTier, curInfo);
        });
    }

    wrapper.dataset.name = name;
    wrapper.dataset.tier = tier;
    wrapper.innerHTML = '';

    const img = await ensureImageInCache(newInfo.path_to_logo_image);
    img.className = 'logo-item';
    img.alt = name;
    wrapper.appendChild(img);

    if (newInfo.price) {
        const basePriceImg = imageCache.get(`assets/png/${newInfo.price}.png`);
        if (basePriceImg) {
            const priceImg = basePriceImg.cloneNode();
            priceImg.className = 'price-tag';
            wrapper.appendChild(priceImg);
        }
    }

    if (newInfo.vegan) {
        const baseVeganImg = imageCache.get('assets/png/Vegan.png');
        if (baseVeganImg) {
            const veganImg = baseVeganImg.cloneNode();
            veganImg.className = 'vegan-tag';
            wrapper.appendChild(veganImg);
        }
    }

    if (activeYearMode) {
        let yearToDisplay = activeYearMode === 'first' ? newInfo.year_first_visited : newInfo.year;
        if (yearToDisplay) {
            let suffix = "";
            const isForced = newInfo.highlighted === "true" || newInfo.highlighted === true;
            if (activeYearMode === 'rerank' && (newInfo.year !== newInfo.year_first_visited || isForced)) {
                suffix = "_highlighted";
            }
            const yearPath = `assets/png/${yearToDisplay}${suffix}.png`;
            const baseYearImg = imageCache.get(yearPath);
            if (baseYearImg) {
                const yearImg = baseYearImg.cloneNode();
                yearImg.className = 'year-tag';
                wrapper.appendChild(yearImg);
            }
        }
    }

    // Move wrapper to correct position in DOM based on globalTierDict
    const tierContent = document.querySelector(`.tier-content[data-tier="${tier}"]`);
    const keys = Object.keys(globalTierDict[tier]);
    keys.forEach(k => {
        const el = (k === name) ? wrapper : document.querySelector(`.logo-item-wrapper[data-name="${k}"]`);
        if (el) {
            tierContent.appendChild(el);
        }
    });

    await saveToServer();
});

init();
