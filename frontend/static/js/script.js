// Inside frontend/static/js/script.js

// --- Helper Functions ---
function escapeHtml(unsafe) {
    if (typeof unsafe !== 'string') return unsafe;
    return unsafe.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#039;");
}
function createListItems(items, listClass = "list-disc list-inside space-y-1 text-gray-700") {
    if (!items || !Array.isArray(items) || items.length === 0) return `<li class="text-gray-500 italic">N/A</li>`; // Ensure items is an array
    return items.map(item => `<li class="ml-4">${escapeHtml(item)}</li>`).join('');
}
function createResultCard(title, contentHtml, cardClasses = "bg-gray-50 p-4 rounded-lg border border-gray-200 shadow-sm") {
     return `<div class="${cardClasses}"><h3 class="text-xl font-semibold text-gray-700 mb-3">${escapeHtml(title)}</h3>${contentHtml}</div>`;
}

// --- Event Listener Setup ---
document.addEventListener('DOMContentLoaded', () => {
    const shopifyForm = document.getElementById('shopify-analyze-form');
    if (shopifyForm) {
        shopifyForm.addEventListener('submit', handleShopifySubmit);
    }
    const socialButtons = document.querySelectorAll('.social-generate-button');
    if (socialButtons.length > 0) {
        socialButtons.forEach(button => button.addEventListener('click', handleSocialGenerate));
        const socialForm = document.getElementById('social-input-form');
        if(socialForm) socialForm.addEventListener('submit', (e) => e.preventDefault()); // Prevent enter submit
    }
});


// --- Shopify Form Handler (No changes needed from previous version) ---
function handleShopifySubmit(event) {
    event.preventDefault();
    console.log("Shopify form submitted");

    const storeUrlInput = document.getElementById('store-url');
    const languageSelect = document.getElementById('language');
    const resultsOutput = document.getElementById('shopify-results-output');
    const loadingIndicator = document.getElementById('shopify-loading');
    const errorMessage = document.getElementById('shopify-error-message');
    const submitButton = document.getElementById('shopify-submit-button');
    const initialMessage = resultsOutput?.querySelector('.initial-message');

    // Basic validation and element checks
    if (!storeUrlInput || !languageSelect || !resultsOutput || !loadingIndicator || !errorMessage || !submitButton) { console.error("Missing Shopify elements"); return; }
    const storeUrl = storeUrlInput.value;
    const language = languageSelect.value;
    if (!storeUrl || !storeUrl.startsWith('http')) { errorMessage.textContent = "Please enter a valid URL"; errorMessage.style.display = 'block'; return; }

    // UI updates
    resultsOutput.innerHTML = ''; if (initialMessage) initialMessage.style.display = 'none';
    errorMessage.style.display = 'none'; errorMessage.textContent = '';
    loadingIndicator.style.display = 'flex'; loadingIndicator.classList.add('flex-col', 'items-center');
    submitButton.disabled = true;

    // Fetch
    fetch('/analyze-shopify', { method: 'POST', headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' }, body: JSON.stringify({ url: storeUrl, language: language }), })
    .then(response => {
        const contentType = response.headers.get("content-type");
        if (contentType && contentType.indexOf("application/json") !== -1) {
            return response.json().then(data => ({ ok: response.ok, status: response.status, jsonData: data }));
        } else {
            return response.text().then(text => { throw new Error(`Server returned non-JSON (Status: ${response.status}): ${text.substring(0,100)}...`); });
        }
    })
    .then(({ ok, status, jsonData }) => {
        if (!ok) { throw new Error(jsonData.error || `HTTP error! Status: ${status}`); }
        loadingIndicator.style.display = 'none'; submitButton.disabled = false;
        displayShopifyResults(jsonData); // Call the updated display function
        console.log('Shopify Success:', jsonData);
     })
    .catch((error) => {
        loadingIndicator.style.display = 'none'; submitButton.disabled = false;
        errorMessage.textContent = `Error: ${error.message}`; errorMessage.style.display = 'block';
        resultsOutput.innerHTML = '<p class="text-center text-red-500">An error occurred.</p>';
        console.error('Shopify Error Details:', error);
    });
}

// --- Social Media Button Handler (No changes needed from previous version) ---
function handleSocialGenerate(event) {
    const button = event.currentTarget;
    const platform = button.dataset.platform;
    console.log(`Social generate button clicked for: ${platform}`);

    // Get inputs from the Social Media form fields
    const topicInput = document.getElementById('social-topic');
    const keywordsInput = document.getElementById('social-keywords');
    const languageSelect = document.getElementById('social-language');

    const resultsOutput = document.getElementById('social-results-output');
    const loadingIndicator = document.getElementById('social-loading');
    const errorMessage = document.getElementById('social-error-message');
    const allButtons = document.querySelectorAll('.social-generate-button');
    const initialMessage = resultsOutput?.querySelector('.initial-message');

    // Validate required elements and topic input
    if (!platform || !topicInput || !languageSelect || !resultsOutput || !loadingIndicator || !errorMessage || !allButtons) {
        console.error("One or more required Social elements not found!");
        if(errorMessage) { errorMessage.textContent = "Internal page error."; errorMessage.style.display = 'block'; }
        return;
    }
    const topic = topicInput.value.trim();
    const keywords = keywordsInput ? keywordsInput.value.trim() : ''; // Get keywords value
    const language = languageSelect.value;

    if (!topic) {
        errorMessage.textContent = "Please enter a topic or description.";
        errorMessage.style.display = 'block';
        return; // Don't proceed if topic is empty
    }

    // UI updates for loading
    if (initialMessage) initialMessage.style.display = 'none';
    errorMessage.style.display = 'none'; errorMessage.textContent = '';
    loadingIndicator.style.display = 'flex'; loadingIndicator.classList.add('flex-col', 'items-center');
    allButtons.forEach(btn => btn.disabled = true);

    // Fetch request with NEW body including topic and keywords
    fetch('/generate-social', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
        body: JSON.stringify({ // Send topic, keywords, language, platform
            platform: platform,
            topic: topic,
            keywords: keywords,
            language: language
        }),
    })
    .then(response => {
        const contentType = response.headers.get("content-type");
        if (contentType && contentType.indexOf("application/json") !== -1) {
            return response.json().then(data => ({ ok: response.ok, status: response.status, jsonData: data }));
        } else {
            return response.text().then(text => { throw new Error(`Server returned non-JSON (Status: ${response.status}): ${text.substring(0,100)}...`); });
        }
     })
    .then(({ ok, status, jsonData }) => {
        if (!ok) { throw new Error(jsonData.error || `HTTP error! Status: ${status}`); }
        loadingIndicator.style.display = 'none'; allButtons.forEach(btn => btn.disabled = false);
        displaySocialResults(jsonData); // Call the updated display function
        console.log('Social Success:', jsonData);
    })
    .catch((error) => {
        loadingIndicator.style.display = 'none'; allButtons.forEach(btn => btn.disabled = false);
        errorMessage.textContent = `Error generating ${platform} content: ${error.message}`; errorMessage.style.display = 'block';
        console.error(`Social Error Details (${platform}):`, error);
    });
}


// --- UPDATED Display function for Shopify SEO Results ---
function displayShopifyResults(data) {
    const resultsOutput = document.getElementById('shopify-results-output');
    if (!resultsOutput) return;
    resultsOutput.innerHTML = ''; // Clear previous results

    // Check for errors returned from the backend
    if (!data || typeof data !== 'object' || data.error) {
        const errorMsg = data?.error ? escapeHtml(data.error) : 'Invalid data format received.';
        resultsOutput.innerHTML = createResultCard("Error", `<p class="text-red-500">${errorMsg}</p>`);
        return;
    }

    // --- Access data from the NEW structured JSON ---
    const coreSeo = data.core_seo || {};
    const contentKeywords = data.content_keywords || {};
    const onPageTechnical = data.on_page_technical || {};
    const schemaRec = onPageTechnical.schema_recommendation || {};

    let outputHtml = '';

    // --- Card 1: Core SEO Critique & Suggestions ---
    let coreSeoContent = `
        <div class="space-y-3">
            <div>
                <p><strong>Current Title Critique:</strong> ${escapeHtml(coreSeo.title_critique || 'N/A')}</p>
                <p><strong>Suggested Title:</strong> <code class="text-sm bg-gray-200 px-1 py-0.5 rounded block break-words">${escapeHtml(coreSeo.suggested_title || 'N/A')}</code></p>
                <p><small><em>Reasoning:</em> ${escapeHtml(coreSeo.title_reasoning || 'N/A')}</small></p>
            </div>
            <hr class="border-gray-200">
            <div>
                <p><strong>Current Description Critique:</strong> ${escapeHtml(coreSeo.description_critique || 'N/A')}</p>
                <p><strong>Suggested Description:</strong> <span class="block border-l-4 border-gray-300 pl-2 mt-1 text-gray-600">${escapeHtml(coreSeo.suggested_description || 'N/A')}</span></p>
                <p><small><em>Reasoning:</em> ${escapeHtml(coreSeo.description_reasoning || 'N/A')}</small></p>
            </div>
             <hr class="border-gray-200">
            <div>
                <p><strong>H1 Analysis:</strong> ${escapeHtml(coreSeo.h1_analysis || 'N/A')}</p>
                ${coreSeo.suggested_h1 ? `<p><strong>Suggested H1:</strong> <code class="text-sm bg-gray-200 px-1 py-0.5 rounded block break-words">${escapeHtml(coreSeo.suggested_h1)}</code></p>` : ''}
            </div>
        </div>`;
    outputHtml += createResultCard("Core SEO Analysis", coreSeoContent);

    // --- Card 2: Content & Keywords ---
    let contentKeywordsContent = `
        <div class="space-y-3">
            <p><strong>Identified Main Topic:</strong> ${escapeHtml(contentKeywords.main_topic || 'N/A')}</p>
            <div><p class="font-semibold">Suggested Keywords:</p><ul class="list-disc list-inside space-y-1 text-gray-700">${createListItems(contentKeywords.suggested_keywords)}</ul></div>
            <div><p class="font-semibold mt-3">Blog Post Ideas:</p><ul class="list-disc list-inside space-y-1 text-gray-700">${createListItems(contentKeywords.blog_post_ideas)}</ul></div>
        </div>`;
    outputHtml += createResultCard("Content & Keywords", contentKeywordsContent);

     // --- Card 3: On-Page & Technical ---
     let onPageTechContent = `
        <div class="space-y-3">
            <div><p class="font-semibold">Image SEO Tip:</p><p>${escapeHtml(onPageTechnical.image_seo_tip || 'N/A')}</p></div>
             <hr class="border-gray-200">
             <div>
                 <p class="font-semibold">Schema Recommendation:</p>
                 <p><strong>Suggested Type:</strong> ${escapeHtml(schemaRec.suggested_type || 'N/A')}</p>
                 ${schemaRec.current_schema_evaluation ? `<p><em>Current Schema Evaluation:</em> ${escapeHtml(schemaRec.current_schema_evaluation)}</p>` : ''}
                 <p class="mt-1"><strong>Essential Properties:</strong></p>
                 <ul class="list-disc list-inside space-y-1 text-gray-700">${createListItems(schemaRec.required_properties)}</ul>
             </div>
             <hr class="border-gray-200">
            <div><p class="font-semibold">Technical SEO Tips:</p><ul class="list-disc list-inside space-y-1 text-gray-700">${createListItems(onPageTechnical.technical_tips)}</ul></div>
        </div>`;
    outputHtml += createResultCard("On-Page & Technical", onPageTechContent);
    // ---

    resultsOutput.innerHTML = outputHtml;
}


// --- UPDATED Display function for Social Media Results ---
function displaySocialResults(data) {
    const resultsOutput = document.getElementById('social-results-output');
    if (!resultsOutput) return;
    const initialMessage = resultsOutput.querySelector('.initial-message');
    if(initialMessage) initialMessage.style.display = 'none';

    // Check for errors
    if (!data || typeof data !== 'object' || data.error) {
        const errorMsg = data?.error ? escapeHtml(data.error) : 'Invalid data format received.';
        const platformName = data?.platform ? ` (${data.platform})` : '';
        resultsOutput.insertAdjacentHTML('afterbegin', createResultCard(`Error${platformName}`, `<p class="text-red-500">${errorMsg}</p>`));
        return;
    }

    const platform = data.platform || 'social'; // Get platform from data
    let cardTitle = `${platform.charAt(0).toUpperCase() + platform.slice(1)} Ideas`;
    let socialContentHtml = '';

    // --- Build HTML based on the platform's specific JSON structure ---
    try {
        if (platform === 'youtube' && data.concepts) {
            socialContentHtml += `<h4 class="text-md font-semibold mb-2 text-gray-600">Video Concepts:</h4>`;
            data.concepts.forEach((concept, index) => {
                socialContentHtml += `
                    <div class="mb-4 pb-3 border-b border-gray-200 last:border-b-0">
                        <p><strong>Concept ${index + 1} Title:</strong> ${escapeHtml(concept.title)}</p>
                        <p><strong>Hook Idea:</strong> ${escapeHtml(concept.hook)}</p>
                        <p><strong>Outline:</p><ul class="list-disc list-inside ml-4">${createListItems(concept.outline)}</ul>
                        <p><strong>Call to Action:</strong> ${escapeHtml(concept.call_to_action)}</p>
                        <p><strong>Thumbnail Idea:</strong> ${escapeHtml(concept.thumbnail_concept)}</p>
                    </div>
                `;
            });
            socialContentHtml += `<div class="mt-3"><strong>Suggested Tags:</strong> <p class="text-sm text-gray-600">${escapeHtml(data.suggested_tags?.join(', '))} </p></div>`;
            socialContentHtml += `<div class="mt-3"><strong>Justification:</strong> <p class="text-sm text-gray-600 italic">${escapeHtml(data.justification)}</p></div>`;

        } else if (platform === 'instagram' && data.post_ideas) {
             socialContentHtml += `<h4 class="text-md font-semibold mb-2 text-gray-600">Post/Reel Ideas:</h4>`;
              data.post_ideas.forEach((idea, index) => {
                  socialContentHtml += `
                      <div class="mb-4 pb-3 border-b border-gray-200 last:border-b-0">
                          <p><strong>Idea ${index + 1} Caption:</strong> ${escapeHtml(idea.caption_idea)}</p>
                          <p><strong>Visual Concept:</strong> ${escapeHtml(idea.visual_concept)}</p>
                          <p><strong>Call to Action:</strong> ${escapeHtml(idea.call_to_action)}</p>
                      </div>
                  `;
              });
            socialContentHtml += `<div class="mt-3"><strong>Suggested Hashtags:</strong> <p class="text-sm text-gray-600">${escapeHtml(data.suggested_hashtags?.join(' '))}</p></div>`;
            socialContentHtml += `<div class="mt-3"><strong>Story Idea:</strong> <p class="text-sm text-gray-600">${escapeHtml(data.story_idea)}</p></div>`;
            socialContentHtml += `<div class="mt-3"><strong>Engagement Tactic:</strong> <p class="text-sm text-gray-600 italic">${escapeHtml(data.engagement_tactic_explanation)}</p></div>`;

        } else if (platform === 'pinterest' && data.pin_concepts) {
             socialContentHtml += `<h4 class="text-md font-semibold mb-2 text-gray-600">Pin Concepts:</h4>`;
              data.pin_concepts.forEach((concept, index) => {
                  socialContentHtml += `
                      <div class="mb-4 pb-3 border-b border-gray-200 last:border-b-0">
                          <p><strong>Concept ${index + 1} Title:</strong> ${escapeHtml(concept.title)}</p>
                          <p><strong>Description:</strong> ${escapeHtml(concept.description)}</p>
                          <p><strong>Visual:</strong> ${escapeHtml(concept.visual_description)}</p>
                      </div>
                  `;
              });
            socialContentHtml += `<div class="mt-3"><strong>Suggested Boards:</strong> <p class="text-sm text-gray-600">${escapeHtml(data.suggested_boards?.join(', '))}</p></div>`;
            socialContentHtml += `<div class="mt-3"><strong>Visual Appeal:</strong> <p class="text-sm text-gray-600 italic">${escapeHtml(data.visual_appeal_explanation)}</p></div>`;

        } else {
            // Fallback for unknown structure or if expected keys are missing
            console.warn("Received social data structure doesn't match expected format for platform:", platform, data);
            socialContentHtml = `<p class="text-orange-600">Could not display structured results. Showing raw data:</p>
                                 <pre class="whitespace-pre-wrap break-words text-sm bg-gray-100 p-3 rounded border border-gray-200">${escapeHtml(JSON.stringify(data, null, 2))}</pre>`;
        }
    } catch (e) {
         console.error("Error processing social data structure:", e);
         socialContentHtml = `<p class="text-red-600">Error displaying results.</p><pre>${escapeHtml(JSON.stringify(data, null, 2))}</pre>`;
    }


    // Prepend new result card
    resultsOutput.insertAdjacentHTML('afterbegin', createResultCard(cardTitle, socialContentHtml));
}