document.addEventListener('DOMContentLoaded', function() {
    // Existing variables
    const timeDisplay = document.getElementById('time-display');
    const settingsButton = document.getElementById('settings-button');
    const settingsModal = document.getElementById('settings-modal');
    const closeModalButton = settingsModal.querySelector('.close-button');
    const timezoneInput = document.getElementById('timezone-input');
    const saveSettingsButton = document.getElementById('save-settings'); // This ID is in the HTML for the main save button in the modal
    const settingsMessage = document.getElementById('settings-message'); // This ID is in the HTML
    const queryInput = document.getElementById('query-input');
    // --- New Elements for Background Settings ---
    const backgroundColorPicker = document.getElementById('backgroundColorPicker');
    const backgroundColorHex = document.getElementById('backgroundColorHex');
    const submitQueryButton = document.getElementById('submit-query');
    const resultsArea = document.getElementById('results-area');
    const scrapedDataPreviewArea = document.getElementById('scraped-data-preview'); // New area to populate

    const TIMEZONE_KEY = 'userTimezone';

    // --- Time and Settings Functions ---
    function openSettingsModal() {
        const currentTz = localStorage.getItem(TIMEZONE_KEY);
        timezoneInput.value = currentTz || '';
        settingsMessage.textContent = '';
        settingsModal.style.display = 'flex';
        loadAppearanceSettings(); // Load current appearance settings when modal opens
    }

    function closeSettingsModal() {
        settingsModal.style.display = 'none';
    }

    async function fetchAndUpdateTime() {
        let userTimezone = localStorage.getItem(TIMEZONE_KEY);
        if (!userTimezone) {
            openSettingsModal();
            userTimezone = 'UTC';
        }
        try {
            const response = await fetch(`/api/time?tz=${encodeURIComponent(userTimezone)}`);
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            timeDisplay.textContent = `${data.time} (${data.timezone_offset})`;
        } catch (error) {
            console.error('Error fetching time:', error);
            timeDisplay.textContent = 'Error';
            if (error.message.toLowerCase().includes("unknown timezone")) {
                 localStorage.removeItem(TIMEZONE_KEY);
                 if(settingsModal.style.display !== 'flex'){ openSettingsModal(); }
                 settingsMessage.textContent = "Invalid timezone. Please enter a valid one.";
            }
        }
    }

    async function handleSaveSettings() {
        // Timezone Saving Part (existing logic)
        let timezoneSaved = false;
        const newTimezone = timezoneInput.value.trim();
        if (newTimezone) { // Only save if there's a value, allowing users to only save appearance
            try {
                const validationResponse = await fetch(`/api/validate_timezone?tz=${encodeURIComponent(newTimezone)}`);
                const validationData = await validationResponse.json();
                if (!validationResponse.ok || !validationData.is_valid) {
                    settingsMessage.textContent = validationData.error || 'Invalid timezone (e.g., "America/New_York").';
                    settingsMessage.style.color = 'red';
                    // Do not return yet, try saving appearance settings
                } else {
                    localStorage.setItem(TIMEZONE_KEY, newTimezone);
                    fetchAndUpdateTime(); // Update time immediately
                    timezoneSaved = true;
                }
            } catch (error) {
                console.error("Error validating timezone:", error);
                settingsMessage.textContent = 'Could not validate timezone. Appearance settings might still be saved.';
                settingsMessage.style.color = 'red';
            }
        }

        // Appearance Saving Part (new logic)
        let appearanceSaved = await saveAppearanceSettings();

        if (timezoneSaved && appearanceSaved) {
            settingsMessage.textContent = 'All settings saved!';
            settingsMessage.style.color = 'green';
            setTimeout(closeSettingsModal, 1500);
        } else if (timezoneSaved) {
            settingsMessage.textContent = 'Timezone saved! (Appearance not saved or no change)';
            settingsMessage.style.color = 'green';
            setTimeout(closeSettingsModal, 1500);
        } else if (appearanceSaved) {
            // Message for appearance saved is handled by saveAppearanceSettings
            setTimeout(closeSettingsModal, 1500);
        } else if (!newTimezone && !appearanceSaved) {
             settingsMessage.textContent = 'No changes to save.';
             settingsMessage.style.color = 'orange';
        }
        // If only one failed, specific error message would have been set by the failed function
    }

    // --- New Functions for Appearance Settings ---
    function getContrastingTextColor(hexColor) {
        if (!hexColor) return '#000000';
        const hex = hexColor.replace('#', '');
        const r = parseInt(hex.substring(0, 2), 16);
        const g = parseInt(hex.substring(2, 4), 16);
        const b = parseInt(hex.substring(4, 6), 16);
        const luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255;
        return luminance > 0.5 ? '#000000' : '#FFFFFF';
    }

    function applySettings(bgColor) {
        document.body.style.backgroundColor = bgColor;
        const textColor = getContrastingTextColor(bgColor);
        document.body.style.color = textColor;
        // Example for specific elements:
        // document.querySelectorAll('.card, .modal-content, .app-header').forEach(el => {
        // el.style.borderColor = textColor === '#000000' ? 'rgba(0,0,0,0.1)' : 'rgba(255,255,255,0.2)';
        // });
        // More targeted styling might be needed for specific components to ensure readability
    }

    async function loadAppearanceSettings() {
        try {
            const response = await fetch('/api/settings');
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            const settings = await response.json();
            if (settings.background_color) {
                applySettings(settings.background_color);
                if (backgroundColorPicker) backgroundColorPicker.value = settings.background_color;
                if (backgroundColorHex) backgroundColorHex.value = settings.background_color;
            }
        } catch (error) {
            console.error("Error loading appearance settings:", error);
            // Don't show modal message here, as it might be confusing during initial page load
        }
    }

    async function saveAppearanceSettings() {
        const colorToSave = backgroundColorHex.value.trim() || backgroundColorPicker.value;
        if (!colorToSave.match(/^#[0-9a-fA-F]{6}$/i) && !colorToSave.match(/^#[0-9a-fA-F]{3}$/i) ) {
            if(backgroundColorHex.value.trim()){ // only show error if user typed something invalid
                 settingsMessage.textContent = 'Invalid HEX color format (e.g., #RRGGBB).';
                 settingsMessage.style.display = 'block';
                 settingsMessage.style.color = 'red';
            }
            return false; // Indicate save failed or no valid color to save
        }

        try {
            const response = await fetch('/api/settings', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ background_color: colorToSave }),
            });
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            const result = await response.json();
            applySettings(colorToSave);
            if (settingsMessage) {
                settingsMessage.textContent = result.message || 'Appearance settings saved!';
                settingsMessage.style.display = 'block';
                settingsMessage.style.color = 'green';
                // setTimeout(() => { settingsMessage.style.display = 'none'; }, 3000); // Timeout handled by main save
            }
            return true; // Indicate save success
        } catch (error) {
            console.error("Error saving appearance settings:", error);
            if (settingsMessage) {
                settingsMessage.textContent = 'Error saving appearance settings.';
                settingsMessage.style.display = 'block';
                settingsMessage.style.color = 'red';
            }
            return false; // Indicate save failed
        }
    }

    // Event Listeners for Appearance
    if (backgroundColorPicker) {
        backgroundColorPicker.addEventListener('input', () => {
            if (backgroundColorHex) backgroundColorHex.value = backgroundColorPicker.value;
        });
    }
    if (backgroundColorHex) {
        backgroundColorHex.addEventListener('input', () => {
            if (backgroundColorHex.value.match(/^#[0-9a-fA-F]{6}$/i) || backgroundColorHex.value.match(/^#[0-9a-fA-F]{3}$/i)) {
                if (backgroundColorPicker) backgroundColorPicker.value = backgroundColorHex.value;
            }
        });
    }

    settingsButton.addEventListener('click', openSettingsModal);
    closeModalButton.addEventListener('click', closeSettingsModal);
    saveSettingsButton.addEventListener('click', handleSaveSettings);
    window.addEventListener('click', function(event) { if (event.target === settingsModal) { closeSettingsModal(); } });
    fetchAndUpdateTime();
    setInterval(fetchAndUpdateTime, 60000);

    // --- Q&A Functionality ---
    function displayResults(data) {
        resultsArea.innerHTML = '';
        if (data.error) {
            resultsArea.innerHTML = `<p class="error-text">Error: ${data.error}</p>`; return;
        }
        if (!data.results || data.results.length === 0) {
            resultsArea.innerHTML = `<p class="placeholder-text">${data.message || "No results found."}</p>`; return;
        }
        const ul = document.createElement('ul');
        ul.className = 'results-list';
        data.results.forEach(resultItem => {
            const item = resultItem.item;
            const li = document.createElement('li');
            li.className = 'result-item';
            const title = document.createElement('h4');
            const link = document.createElement('a');
            link.href = item.url; link.textContent = item.title; link.target = '_blank';
            title.appendChild(link);
            const summary = document.createElement('p');
            summary.textContent = item.summary.substring(0, 250) + (item.summary.length > 250 ? '...' : '');
            const source = document.createElement('span');
            source.className = 'source';
            source.textContent = `Source: ${item.source} | Score: ${resultItem.score.toFixed(2)}`;
            const scrapedAt = document.createElement('span');
            scrapedAt.className = 'source';
            try { scrapedAt.textContent = ` | Scraped: ${new Date(item.scraped_at).toLocaleString()}`; } catch(e){}
            li.appendChild(title); li.appendChild(summary); li.appendChild(source); li.appendChild(scrapedAt);
            ul.appendChild(li);
        });
        resultsArea.appendChild(ul);
    }

    async function handleQuerySubmit() {
        const query = queryInput.value.trim();
        if (!query) { resultsArea.innerHTML = '<p class="placeholder-text">Please enter a query.</p>'; return; }
        resultsArea.innerHTML = '<p class="placeholder-text">Searching...</p>';
        try {
            const response = await fetch('/api/query', {
                method: 'POST', headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ query: query }),
            });
            const responseData = await response.json();
            displayResults(responseData);
        } catch (error) {
            console.error('Error submitting query:', error);
            resultsArea.innerHTML = `<p class="error-text">An error occurred. Please try again.</p>`;
        }
    }
    submitQueryButton.addEventListener('click', handleQuerySubmit);
    queryInput.addEventListener('keypress', function(event) { if (event.key === 'Enter') { handleQuerySubmit(); }});

    // --- Scraped Data Preview (Implemented for Step 9) ---
    async function loadScrapedDataPreview() {
        scrapedDataPreviewArea.innerHTML = '<p class="placeholder-text">Loading recent data...</p>';
        try {
            const response = await fetch('/api/data'); // Endpoint returns all data
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
            }
            const allData = await response.json();

            if (!allData || allData.length === 0) {
                scrapedDataPreviewArea.innerHTML = '<p class="placeholder-text">No data has been scraped yet.</p>';
                return;
            }

            // Sort data by scraped_at date, most recent first
            allData.sort((a, b) => new Date(b.scraped_at) - new Date(a.scraped_at));

            const recentData = allData.slice(0, 5); // Display top 5 most recent

            scrapedDataPreviewArea.innerHTML = ''; // Clear loading text
            if (recentData.length === 0) { // Should not happen if allData had items, but good check
                 scrapedDataPreviewArea.innerHTML = '<p class="placeholder-text">No recent data to display.</p>';
                 return;
            }

            const ul = document.createElement('ul');
            ul.className = 'data-item-list'; // Similar to results-list or define new style

            recentData.forEach(item => {
                const li = document.createElement('li');
                li.className = 'data-item'; // Use class from style.css (same as result-item)

                const title = document.createElement('h4');
                const link = document.createElement('a');
                link.href = item.url;
                link.textContent = item.title;
                link.target = '_blank';
                title.appendChild(link);

                const summary = document.createElement('p');
                // Shorter summary for preview
                summary.textContent = item.summary.substring(0, 150) + (item.summary.length > 150 ? '...' : '');

                const source = document.createElement('span');
                source.className = 'source';
                source.textContent = `Source: ${item.source}`;

                const scrapedAt = document.createElement('span');
                scrapedAt.className = 'source';
                 try { scrapedAt.textContent = ` | Scraped: ${new Date(item.scraped_at).toLocaleString()}`; } catch(e){}


                li.appendChild(title);
                li.appendChild(summary);
                li.appendChild(source);
                li.appendChild(scrapedAt);
                ul.appendChild(li);
            });
            scrapedDataPreviewArea.appendChild(ul);

        } catch (error) {
            console.error('Error loading scraped data preview:', error);
            scrapedDataPreviewArea.innerHTML = `<p class="error-text">Could not load recent data: ${error.message}</p>`;
        }
    }

    // Initial calls
    loadScrapedDataPreview(); // Load preview data on page load
    loadAppearanceSettings(); // Load appearance settings on page load
});
