# /content/text-generation-webui/modules/custom_ui.py
import gradio as gr

def inject_custom_ui():
    """
    Returns a Gradio HTML component with CSS and JS that:
      - restyles the chat input to be prettier
      - moves the 'Git' button into a higher position near the input
      - adds some small animations / rounded styling
    Call this function somewhere inside your Gradio layout (inside the same Blocks context).
    """
    html = r"""
    <style>
    /* ---------- Chat input styling ---------- */
    /* container that holds the input textarea (try to cover common gradio class names) */
    .chat-input, .input-area, .gradio-textbox, textarea {
        border-radius: 14px !important;
        box-shadow: 0 6px 24px rgba(0,0,0,0.45) !important;
    }

    /* textarea look */
    textarea {
        min-height: 220px !important;
        max-height: 420px !important;
        padding: 18px !important;
        font-size: 15px !important;
        line-height: 1.45 !important;
        background: linear-gradient(180deg, #1f2326 0%, #151618 100%) !important;
        color: #e6eef6 !important;
        border: 1px solid rgba(255,255,255,0.04) !important;
        transition: transform .12s ease, box-shadow .12s ease;
        resize: vertical !important;
    }

    textarea:focus {
        transform: translateY(-2px);
        box-shadow: 0 10px 30px rgba(0,0,0,0.6), 0 0 0 3px rgba(100,150,255,0.04);
        outline: none !important;
        border-color: rgba(100,150,255,0.22) !important;
    }

    /* Send button styling: try to cover common button classes used by gradio */
    button.send, button[aria-label="Send"], .send-btn, button[type="submit"] {
        border-radius: 12px !important;
        padding: 8px 14px !important;
        font-weight: 600 !important;
        box-shadow: 0 6px 18px rgba(0,0,0,0.45) !important;
        background: linear-gradient(180deg, #2f7bdc, #1a5fd5) !important;
        color: white !important;
        border: none !important;
    }

    /* Git button styling after relocation */
    .moved-git-btn {
        margin-left: 10px;
        margin-bottom: 6px;
        border-radius: 10px;
        padding: 6px 10px;
        font-weight: 600;
        box-shadow: 0 6px 18px rgba(0,0,0,0.35);
        background: linear-gradient(180deg, #33353a, #212226);
        color: #f0f4f8;
        border: 1px solid rgba(255,255,255,0.04);
        cursor: pointer;
    }

    /* Responsiveness: ensure the repositioned git button doesn't break small screens */
    @media (max-width: 900px) {
        .moved-git-btn { display: inline-block; margin-top: 6px; }
        textarea { min-height: 160px !important; }
    }
    </style>

    <script>
    // Wait for the page and Gradio elements to exist
    (function waitForGradio() {
        const tries = 40;
        let i = 0;
        function attempt() {
            i++;
            // locate probable textarea input
            let textArea = document.querySelector('textarea');
            // locate buttons that might be labelled 'Git' or contain 'Git'
            let allButtons = Array.from(document.querySelectorAll('button'));
            let gitButton = allButtons.find(b => {
                if (!b) return false;
                const t = (b.innerText || "").trim().toLowerCase();
                if (t === 'git' || t.includes('git')) return true;
                // some gradio buttons use aria-label
                const aria = (b.getAttribute && b.getAttribute('aria-label') || "").toLowerCase();
                if (aria === 'git' || aria.includes('git')) return true;
                return false;
            });

            if (!textArea) {
                // still waiting
                if (i < tries) setTimeout(attempt, 250);
                return;
            }

            // styling: add a helper css class to the textarea (if available)
            try {
                textArea.classList.add('chat-input');
            } catch(e){}

            // If we found the git button, move it above the input area to a better place
            if (gitButton) {
                // add a mark class for consistent styling
                gitButton.classList.add('moved-git-btn');

                // find a reasonable container near the text area to insert before
                // try ancestors of the textarea
                let targetContainer = textArea.closest('.chat-input, .input-area, .svelte-1, .gradio-container');
                if (!targetContainer) {
                    // fallback: use the parent of the textarea
                    targetContainer = textArea.parentElement;
                }
                // create wrapper if needed
                let wrapper = document.createElement('div');
                wrapper.style.display = 'flex';
                wrapper.style.alignItems = 'center';
                wrapper.style.gap = '6px';
                wrapper.style.marginBottom = '4px';

                // Move the gitButton to the wrapper and place it right before the textarea container
                try {
                    // Avoid duplicates: remove previous occurences we may have injected
                    let prev = document.querySelectorAll('.moved-git-btn');
                    if (prev && prev.length > 1) {
                        for (let idx = 0; idx < prev.length-1; idx++) prev[idx].remove();
                    }

                    // insert wrapper above the textarea parent
                    textArea.parentElement.parentElement.insertBefore(wrapper, textArea.parentElement);
                    // append the git button into the wrapper
                    wrapper.appendChild(gitButton);
                    // optional: add a small label next to it (comment out if you don't want)
                    // let label = document.createElement('span');
                    // label.innerText = 'Git actions';
                    // label.style.color = '#cbd6e8';
                    // label.style.fontSize = '13px';
                    // label.style.marginLeft = '6px';
                    // wrapper.appendChild(label);
                } catch(e) {
                    console.warn('custom_ui: could not relocate git button', e);
                }
            } else {
                // If we didn't find the git button yet, try a couple more times (it may be rendered later)
                if (i < tries) setTimeout(attempt, 250);
            }
        }
        attempt();
    })();
    </script>
    """

    return gr.HTML(html)
