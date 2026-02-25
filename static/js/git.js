// ================================================================
// GIZMO AI v3.5.2 - Fixed Git Button JavaScript
// Location: /content/text-generation-webui/static/js/git.js
// ================================================================

document.addEventListener('DOMContentLoaded', function(){
  const gitBtn = document.getElementById('git-button');
  if(!gitBtn) {
    console.log('[Git] No git-button element found');
    return;
  }

  console.log('[Git] Initializing git button for v3.5.2');

  const ensureMenu = () => {
    let gitMenu = document.getElementById('git-menu');
    if(!gitMenu){
      gitMenu = document.createElement('div');
      gitMenu.id = 'git-menu';
      gitMenu.style.cssText = `
        position: absolute;
        right: 20px;
        top: ${gitBtn.getBoundingClientRect().bottom + window.scrollY + 6}px;
        background: white;
        border: 1px solid #ddd;
        padding: 10px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        z-index: 2000;
        border-radius: 6px;
        min-width: 200px;
      `;
      
      gitMenu.innerHTML = `
        <div style="display:flex;flex-direction:column;gap:8px;">
          <button id="git-status-btn" class="git-menu-btn">📊 View Status</button>
          <button id="git-pull-btn" class="git-menu-btn">⬇️ Pull Latest</button>
          <button id="git-push-btn" class="git-menu-btn">⬆️ Push Changes</button>
          <button id="git-branch-btn" class="git-menu-btn">🌿 Create Branch</button>
        </div>
      `;
      
      const style = document.createElement('style');
      style.textContent = `
        .git-menu-btn {
          padding: 10px;
          border: 1px solid #ddd;
          background: #f8f9fa;
          border-radius: 4px;
          cursor: pointer;
          text-align: left;
          font-size: 13px;
          transition: all 0.2s;
        }
        .git-menu-btn:hover {
          background: #e9ecef;
          border-color: #adb5bd;
        }
        .git-menu-btn:active {
          background: #dee2e6;
        }
      `;
      document.head.appendChild(style);
      
      document.body.appendChild(gitMenu);
    }
    return gitMenu;
  };

  gitBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    const menu = ensureMenu();
    const isVisible = menu.style.display === 'block';
    menu.style.display = isVisible ? 'none' : 'block';
    console.log('[Git] Menu toggled:', !isVisible);
  });

  document.addEventListener('click', (e) => {
    const menu = document.getElementById('git-menu');
    if(menu && !e.target.closest('#git-button') && !e.target.closest('#git-menu')){
      menu.style.display = 'none';
    }
  });

  document.addEventListener('click', async (e) => {
    const target = e.target;
    
    if(target && target.id === 'git-status-btn'){
      console.log('[Git] Fetching status...');
      try {
        const response = await fetch('/git/status', {
          method: 'GET',
          headers: { 'Content-Type': 'application/json' }
        });
        const data = await response.json();
        
        if(data.ok){
          let msg = '📊 Git Status\n\n';
          msg += `Branch: ${data.branch || 'unknown'}\n\n`;
          
          if(data.modified && data.modified.length > 0){
            msg += '📝 Modified files:\n';
            data.modified.forEach(f => msg += `  • ${f}\n`);
          }
          
          if(data.untracked && data.untracked.length > 0){
            msg += '\n📄 Untracked files:\n';
            data.untracked.forEach(f => msg += `  • ${f}\n`);
          }
          
          if(data.staged && data.staged.length > 0){
            msg += '\n✅ Staged files:\n';
            data.staged.forEach(f => msg += `  • ${f}\n`);
          }
          
          if((!data.modified || data.modified.length === 0) && 
             (!data.untracked || data.untracked.length === 0) &&
             (!data.staged || data.staged.length === 0)){
            msg += '✅ Working directory clean!';
          }
          
          alert(msg);
        } else {
          alert('❌ Error: ' + (data.error || 'Failed to get status'));
        }
      } catch(err) {
        console.error('[Git] Status error:', err);
        alert('❌ Network error: ' + err.message);
      }
    }
    
    if(target && target.id === 'git-pull-btn'){
      if(!confirm('Pull latest changes from remote?\n\nThis will update your local files.')){
        return;
      }
      
      console.log('[Git] Pulling changes...');
      try {
        const response = await fetch('/git/pull', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' }
        });
        const data = await response.json();
        
        if(data.ok){
          alert('✅ Pull successful!\n\n' + (data.message || 'Changes pulled from remote'));
        } else {
          alert('❌ Error: ' + (data.error || 'Pull failed'));
        }
      } catch(err) {
        console.error('[Git] Pull error:', err);
        alert('❌ Network error: ' + err.message);
      }
    }
    
    if(target && target.id === 'git-push-btn'){
      const branch = prompt('Push to which branch?\n(leave blank for current branch)');
      if(branch === null) return;
      
      const message = prompt('Commit message:', 'Update from Gizmo AI');
      if(message === null) return;
      
      console.log('[Git] Pushing changes...');
      try {
        const response = await fetch('/git/push', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            branch: branch || null,
            message: message || 'Update from Gizmo AI'
          })
        });
        const data = await response.json();
        
        if(data.ok){
          if(data.already_up_to_date){
            alert('✅ Already up to date\n\nNo changes to commit');
          } else {
            alert('✅ Push successful!\n\nChanges pushed to ' + (data.branch || 'remote'));
          }
        } else {
          alert('❌ Error: ' + (data.error || 'Push failed'));
        }
      } catch(err) {
        console.error('[Git] Push error:', err);
        alert('❌ Network error: ' + err.message);
      }
    }
    
    if(target && target.id === 'git-branch-btn'){
      const branchName = prompt('Enter new branch name:\n(e.g., feature/my-feature)');
      if(!branchName || !branchName.trim()) return;
      
      const baseBranch = prompt('Create from which branch?', 'main');
      if(baseBranch === null) return;
      
      console.log('[Git] Creating branch:', branchName);
      try {
        const response = await fetch('/git/create-branch', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            branch: branchName.trim(),
            base: baseBranch.trim() || 'main'
          })
        });
        const data = await response.json();
        
        if(data.ok){
          alert('✅ Branch created!\n\n' + data.message);
        } else {
          alert('❌ Error: ' + (data.error || 'Failed to create branch'));
        }
      } catch(err) {
        console.error('[Git] Branch error:', err);
        alert('❌ Network error: ' + err.message);
      }
    }
  });

  console.log('[Git] Button initialized successfully for Gizmo v3.5.2');
});
