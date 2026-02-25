document.addEventListener('DOMContentLoaded', function(){
  const gitBtn = document.getElementById('git-button');
  if(!gitBtn) return; // nothing to do

  const ensureMenu = () => {
    let gitMenu = document.getElementById('git-menu');
    if(!gitMenu){
      gitMenu = document.createElement('div');
      gitMenu.id = 'git-menu';
      gitMenu.style.position = 'absolute';
      gitMenu.style.right = '20px';
      gitMenu.style.top = (gitBtn.getBoundingClientRect().bottom + window.scrollY + 6) + 'px';
      gitMenu.style.background = 'white';
      gitMenu.style.border = '1px solid #ddd';
      gitMenu.style.padding = '8px';
      gitMenu.style.boxShadow = '0 4px 12px rgba(0,0,0,0.08)';
      gitMenu.style.zIndex = 2000;
      gitMenu.innerHTML = `
        <div style="display:flex;flex-direction:column;gap:6px;min-width:180px;">
          <button id="create-branch-btn">Create branch</button>
          <button id="push-changes-btn">Push current changes</button>
        </div>
      `;
      document.body.appendChild(gitMenu);
    }
    return gitMenu;
  };

  gitBtn.addEventListener('click', (e)=>{
    e.stopPropagation();
    const menu = ensureMenu();
    menu.classList.toggle('visible');
    menu.style.display = menu.classList.contains('visible') ? 'block' : 'none';
  });

  // close when clicking outside
  document.addEventListener('click', (e)=>{
    const menu = document.getElementById('git-menu');
    if(menu && !e.target.closest('#git-button') && !e.target.closest('#git-menu')){
      menu.classList.remove('visible');
      menu.style.display = 'none';
    }
  });

  // handle menu actions
  document.addEventListener('click', (e)=>{
    if(e.target && e.target.id === 'create-branch-btn'){
      const branch = prompt('Enter new branch name (eg. feature/xyz)');
      if(!branch) return;
      // Optionally ask token (recommended to set as env var instead)
      const token = null; // do not prompt by default; backend will pick env var
      fetch('/git/create-branch', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ branch: branch, base: 'main' })
      }).then(r=> r.json()).then(j=>{
        if(j.ok) alert('Branch created: ' + j.branch);
        else alert('Error: ' + (j.error || JSON.stringify(j)));
      }).catch(err=>{
        alert('Network error: ' + err);
      });
    }

    if(e.target && e.target.id === 'push-changes-btn'){
      const branch = prompt('Push to which branch? (leave blank to use current branch)');
});
