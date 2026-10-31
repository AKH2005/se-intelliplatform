# Master redesign script for UserModeWorkspace.tsx into a cohesive 5-option Beginner Mode workspace

import re

with open('frontend/src/views/UserModeWorkspace.tsx', 'r', encoding='utf-8') as f:
    text = f.read()

# We need to extract the sections:
# 1. Stepper: lines from '{/* 1. Guided Journey Stepper' to before '{/* 2. Welcoming Home Dashboard'
# 2. Hero + 3 Choices: from '{/* 2. Welcoming Home Dashboard' to before '{/* 3. Synthesized Blueprint Review'
# 3. Blueprint: from '{/* 3. Synthesized Blueprint Review' to before '{/* 5. Live Application Preview'
# 4. Live Preview: from '{/* 5. Live Application Preview' to before '{/* 6. My Projects Section'
# 5. Gallery: from '{/* 6. My Projects Section' to before '{/* 7. Explore & Learn'
# 6. Learn: from '{/* 7. Explore & Learn' to before '</main>'

stepper_marker = "{/* 1. Guided Journey Stepper (Stages 1 through 6)                     */}"
hero_marker = "{/* 2. Welcoming Home Dashboard & Hero Section                        */}"
blueprint_marker = "{/* 3. Synthesized Blueprint Review Card (Stage 3)                    */}"
live_marker = "{/* 5. Live Application Preview & Refinement Viewport (Stages 5 & 6)   */}"
gallery_marker = "{/* 6. My Projects Section                                            */}"
learn_marker = "{/* 7. Explore & Learn Section                                        */}"
main_close_marker = "      </main>\n    </div>"

idx_stepper = text.find(stepper_marker)
idx_hero = text.find(hero_marker)
idx_blueprint = text.find(blueprint_marker)
idx_live = text.find(live_marker)
idx_gallery = text.find(gallery_marker)
idx_learn = text.find(learn_marker)
idx_main_close = text.rfind(main_close_marker)

print(f"Indices: stepper={idx_stepper}, hero={idx_hero}, blueprint={idx_blueprint}, live={idx_live}, gallery={idx_gallery}, learn={idx_learn}, main_close={idx_main_close}")

if not all(x != -1 for x in [idx_stepper, idx_hero, idx_blueprint, idx_live, idx_gallery, idx_learn, idx_main_close]):
    print("Could not find all markers.")
    exit(1)

stepper_block = text[idx_stepper:idx_hero].strip()
hero_block = text[idx_hero:idx_blueprint].strip()
blueprint_block = text[idx_blueprint:idx_live].strip()
live_block = text[idx_live:idx_gallery].strip()
gallery_block = text[idx_gallery:idx_learn].strip()
learn_block = text[idx_learn:idx_main_close].strip()

# Adjust conditions:
# In stepper: allow it whenever planResult or isBuildingApp or activeCreationMode !== 'ai'
stepper_block = stepper_block.replace(
    "{(planResult || isBuildingApp || isViewingLiveApp || activeCreationMode !== 'ai') && (",
    "{(planResult || isBuildingApp || activeCreationMode !== 'ai') && ("
)

# In hero: allow it when not planResult and not isBuildingApp
hero_block = hero_block.replace(
    "{!planResult && !isBuildingApp && !isViewingLiveApp && (",
    "{!planResult && !isBuildingApp && ("
)

# In blueprint:
blueprint_block = blueprint_block.replace(
    "{planResult && !isBuildingApp && !isViewingLiveApp && (",
    "{planResult && !isBuildingApp && ("
)

# In gallery: add quick buttons (Overview, Code, Download ZIP)
new_gallery_extra_buttons = """<button
                          type="button"
                          onClick={() => {
                            selectProject(proj);
                            setActiveTab('overview');
                          }}
                          style={{
                            background: 'rgba(56, 189, 248, 0.1)',
                            border: '1px solid rgba(56, 189, 248, 0.25)',
                            borderRadius: '6px',
                            padding: '0.35rem 0.6rem',
                            color: '#38bdf8',
                            fontSize: '0.78rem',
                            fontWeight: 600,
                            cursor: 'pointer',
                          }}
                        >
                          Overview
                        </button>

                        <button
                          type="button"
                          onClick={() => {
                            selectProject(proj);
                            setActiveTab('code-studio');
                          }}
                          style={{
                            background: 'rgba(6, 182, 212, 0.1)',
                            border: '1px solid rgba(6, 182, 212, 0.25)',
                            borderRadius: '6px',
                            padding: '0.35rem 0.6rem',
                            color: '#22d3ee',
                            fontSize: '0.78rem',
                            fontWeight: 600,
                            cursor: 'pointer',
                          }}
                        >
                          Code
                        </button>

                        <button
                          type="button"
                          onClick={() => handleDownloadZip(proj)}
                          title="Download project code as ZIP"
                          style={{
                            background: 'rgba(255, 255, 255, 0.05)',
                            border: '1px solid rgba(255, 255, 255, 0.12)',
                            borderRadius: '6px',
                            padding: '0.35rem 0.55rem',
                            color: '#94a3b8',
                            fontSize: '0.78rem',
                            cursor: 'pointer',
                            display: 'flex',
                            alignItems: 'center',
                            gap: '0.25rem',
                          }}
                        >
                          <Download size={12} />
                          <span>ZIP</span>
                        </button>

                        """

gallery_block = gallery_block.replace(
    "<div style={{ display: 'flex', alignItems: 'center', gap: '0.45rem' }}>",
    "<div style={{ display: 'flex', alignItems: 'center', gap: '0.45rem', flexWrap: 'wrap' }}>\n                        " + new_gallery_extra_buttons
)

# In live_block:
# Allow live_block to render for (createdProject || currentProject)
live_block = live_block.replace(
    "{isViewingLiveApp && createdProject && (",
    "{(isViewingLiveApp || activeTab === 'preview') && (createdProject || currentProject) && ("
)
live_block = live_block.replace("createdProject.name", "(createdProject || currentProject)?.name || 'Application'")

# Construct Overview Tab JSX
overview_tab_jsx = """{/* ================================================================= */}
        {/* TAB 2: Project Overview & Health                                  */}
        {/* ================================================================= */}
        {activeTab === 'overview' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.75rem', maxWidth: '1240px', width: '100%', margin: '0 auto' }}>
            {/* Hero Header */}
            <div
              style={{
                background: 'linear-gradient(135deg, rgba(99, 102, 241, 0.18), rgba(13, 18, 31, 0.95))',
                border: '1px solid rgba(99, 102, 241, 0.35)',
                borderRadius: '20px',
                padding: '2rem',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                flexWrap: 'wrap',
                gap: '1.25rem',
                boxShadow: '0 12px 35px rgba(0, 0, 0, 0.4)',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '1.25rem' }}>
                <div
                  style={{
                    width: 52,
                    height: 52,
                    borderRadius: '14px',
                    background: 'linear-gradient(135deg, #6366f1, #8b5cf6)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: '#ffffff',
                    boxShadow: '0 4px 14px rgba(99, 102, 241, 0.4)',
                  }}
                >
                  <Compass size={26} />
                </div>
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem', flexWrap: 'wrap' }}>
                    <h1 style={{ fontSize: '1.5rem', fontWeight: 800, margin: 0, color: '#ffffff', letterSpacing: '-0.02em' }}>
                      {currentProject?.name || 'Application Overview'}
                    </h1>
                    <span
                      style={{
                        fontSize: '0.72rem',
                        fontWeight: 700,
                        padding: '0.2rem 0.6rem',
                        borderRadius: '9999px',
                        background: 'rgba(16, 185, 129, 0.18)',
                        color: '#34d399',
                        border: '1px solid rgba(16, 185, 129, 0.35)',
                      }}
                    >
                      ACTIVE
                    </span>
                    <span
                      style={{
                        fontSize: '0.72rem',
                        fontWeight: 700,
                        padding: '0.2rem 0.6rem',
                        borderRadius: '6px',
                        background: 'rgba(139, 92, 246, 0.18)',
                        color: '#c4b5fd',
                        border: '1px solid rgba(139, 92, 246, 0.35)',
                      }}
                    >
                      v{activeVersionNum}.0
                    </span>
                  </div>
                  <p style={{ fontSize: '0.88rem', color: '#94a3b8', margin: '0.4rem 0 0 0', maxWidth: '680px', lineHeight: 1.5 }}>
                    {currentProject?.description || 'Autonomous AI-built application managed seamlessly on SE IntelliPlatform.'}
                  </p>
                </div>
              </div>

              {/* Action Buttons */}
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem', flexWrap: 'wrap' }}>
                <Button
                  variant="primary"
                  onClick={() => {
                    if (currentProject) handleLaunchProjectPreview(currentProject);
                    else setActiveTab('preview');
                  }}
                  icon={<Play size={14} />}
                  style={{ background: 'linear-gradient(135deg, #10b981, #06b6d4)', fontWeight: 650, boxShadow: '0 4px 14px rgba(16, 185, 129, 0.3)' }}
                >
                  Open Live Preview
                </Button>
                <Button
                  variant="secondary"
                  onClick={() => setActiveTab('code-studio')}
                  icon={<Code2 size={14} />}
                  style={{ background: 'rgba(255, 255, 255, 0.06)', border: '1px solid rgba(255, 255, 255, 0.12)' }}
                >
                  View Code
                </Button>
                <Button
                  variant="secondary"
                  onClick={() => handleDownloadZip(currentProject)}
                  icon={<Download size={14} />}
                  disabled={isDownloadingZip}
                  style={{ background: 'rgba(255, 255, 255, 0.06)', border: '1px solid rgba(255, 255, 255, 0.12)' }}
                >
                  {isDownloadingZip ? 'Downloading...' : 'Download ZIP'}
                </Button>
                <Button
                  variant="secondary"
                  onClick={() => {
                    if (currentProject) handleOpenInDeveloperMode(currentProject);
                    else switchMode('developer');
                  }}
                  icon={<ArrowRight size={14} />}
                  style={{ background: 'rgba(99, 102, 241, 0.12)', border: '1px solid rgba(99, 102, 241, 0.3)', color: '#c7d2fe' }}
                >
                  Developer Mode
                </Button>
              </div>
            </div>

            {/* Metrics and Health Grid */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1.25rem' }}>
              <div
                style={{
                  background: 'rgba(15, 20, 36, 0.75)',
                  border: '1px solid rgba(255, 255, 255, 0.08)',
                  borderRadius: '16px',
                  padding: '1.5rem',
                  backdropFilter: 'blur(12px)',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.75rem' }}>
                  <ShieldCheck size={18} color="#10b981" />
                  <span style={{ fontSize: '0.8rem', fontWeight: 700, color: '#f8fafc', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                    Runtime Health
                  </span>
                </div>
                <div style={{ fontSize: '1.6rem', fontWeight: 800, color: '#34d399', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <span style={{ width: 8, height: 8, borderRadius: '50%', background: '#10b981', boxShadow: '0 0 10px #10b981' }} />
                  <span>Port {runtimePort} Live</span>
                </div>
                <p style={{ fontSize: '0.8rem', color: '#94a3b8', margin: '0.45rem 0 0 0' }}>
                  Application container is healthy. Response latency &lt; 45ms.
                </p>
              </div>

              <div
                style={{
                  background: 'rgba(15, 20, 36, 0.75)',
                  border: '1px solid rgba(255, 255, 255, 0.08)',
                  borderRadius: '16px',
                  padding: '1.5rem',
                  backdropFilter: 'blur(12px)',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.75rem' }}>
                  <GitBranch size={18} color="#818cf8" />
                  <span style={{ fontSize: '0.8rem', fontWeight: 700, color: '#f8fafc', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                    Active Version
                  </span>
                </div>
                <div style={{ fontSize: '1.6rem', fontWeight: 800, color: '#c4b5fd' }}>
                  Version {activeVersionNum}.0
                </div>
                <p style={{ fontSize: '0.8rem', color: '#94a3b8', margin: '0.45rem 0 0 0' }}>
                  All modifications tracked with immutable version snapshots and instant rollback.
                </p>
              </div>

              <div
                style={{
                  background: 'rgba(15, 20, 36, 0.75)',
                  border: '1px solid rgba(255, 255, 255, 0.08)',
                  borderRadius: '16px',
                  padding: '1.5rem',
                  backdropFilter: 'blur(12px)',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.75rem' }}>
                  <FileCode size={18} color="#06b6d4" />
                  <span style={{ fontSize: '0.8rem', fontWeight: 700, color: '#f8fafc', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                    Source Export
                  </span>
                </div>
                <div style={{ fontSize: '1.6rem', fontWeight: 800, color: '#22d3ee' }}>
                  ZIP Ready
                </div>
                <p style={{ fontSize: '0.8rem', color: '#94a3b8', margin: '0.45rem 0 0 0' }}>
                  Complete frontend, backend, and configs packaged without credentials.
                </p>
              </div>
            </div>

            {/* Non-Technical Summary & Features */}
            <div
              style={{
                background: 'rgba(15, 20, 36, 0.75)',
                border: '1px solid rgba(255, 255, 255, 0.08)',
                borderRadius: '18px',
                padding: '1.75rem',
              }}
            >
              <h3 style={{ fontSize: '1.15rem', fontWeight: 700, margin: '0 0 0.85rem 0', color: '#ffffff' }}>
                Application Summary
              </h3>
              <p style={{ fontSize: '0.9rem', color: '#cbd5e1', lineHeight: 1.6, margin: '0 0 1.35rem 0' }}>
                {currentProject?.description || 'Your application is built with a reactive frontend and FastAPI backend routes, serving users through the container runtime.'}
              </p>

              <h4 style={{ fontSize: '0.95rem', fontWeight: 650, margin: '0 0 0.85rem 0', color: '#818cf8' }}>
                Core Capabilities & Architecture
              </h4>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '0.85rem' }}>
                {[
                  'Adaptive responsive UI supporting desktop, tablet, and mobile',
                  'FastAPI backend with structured schema validation and error handling',
                  'Containerized isolated execution environment on Port 8001',
                  'Instant natural-language continuous app refinement support',
                  'Version-controlled snapshot tracking with one-click rollback',
                  'One-click sanitized ZIP source code export for offline deployment',
                ].map((feat, i) => (
                  <div
                    key={i}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.55rem',
                      padding: '0.75rem 1rem',
                      background: 'rgba(255, 255, 255, 0.02)',
                      border: '1px solid rgba(255, 255, 255, 0.06)',
                      borderRadius: '10px',
                      fontSize: '0.84rem',
                      color: '#e2e8f0',
                    }}
                  >
                    <CheckCircle2 size={16} color="#10b981" />
                    <span>{feat}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Version History & Rollback Timeline */}
            <div
              style={{
                background: 'rgba(15, 20, 36, 0.75)',
                border: '1px solid rgba(255, 255, 255, 0.08)',
                borderRadius: '18px',
                padding: '1.75rem',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem', flexWrap: 'wrap', gap: '0.5rem' }}>
                <div>
                  <h3 style={{ fontSize: '1.15rem', fontWeight: 700, margin: 0, color: '#ffffff' }}>
                    Version History & Snapshots
                  </h3>
                  <p style={{ fontSize: '0.82rem', color: '#94a3b8', margin: '0.25rem 0 0 0' }}>
                    Every change generates an immutable snapshot. You can roll back anytime without data loss.
                  </p>
                </div>
                {activeVersionNum > 1 && (
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={handleRollback}
                    icon={<RotateCcw size={13} />}
                    disabled={isApplyingChange}
                    style={{ background: 'rgba(239, 68, 68, 0.12)', border: '1px solid rgba(239, 68, 68, 0.3)', color: '#fca5a5' }}
                  >
                    {isApplyingChange ? 'Rolling back...' : `Roll back to v${activeVersionNum - 1}`}
                  </Button>
                )}
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                {Array.from({ length: Math.max(activeVersionNum, 1) }, (_, i) => activeVersionNum - i).map((ver) => (
                  <div
                    key={ver}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      padding: '0.85rem 1.15rem',
                      borderRadius: '12px',
                      background: ver === activeVersionNum ? 'rgba(99, 102, 241, 0.12)' : 'rgba(255, 255, 255, 0.02)',
                      border: ver === activeVersionNum ? '1px solid rgba(99, 102, 241, 0.35)' : '1px solid rgba(255, 255, 255, 0.05)',
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.85rem' }}>
                      <span
                        style={{
                          fontSize: '0.75rem',
                          fontWeight: 700,
                          padding: '0.2rem 0.55rem',
                          borderRadius: '6px',
                          background: ver === activeVersionNum ? 'rgba(16, 185, 129, 0.2)' : 'rgba(255, 255, 255, 0.06)',
                          color: ver === activeVersionNum ? '#34d399' : '#94a3b8',
                        }}
                      >
                        v{ver}
                      </span>
                      <div>
                        <span style={{ fontSize: '0.88rem', fontWeight: 600, color: '#f8fafc' }}>
                          {ver === 1 ? 'Initial Blueprint Scaffold' : `AI Refinement #${ver - 1}`}
                        </span>
                        <span style={{ fontSize: '0.75rem', color: '#64748b', marginLeft: '0.65rem' }}>
                          {ver === activeVersionNum ? '● Active Version' : 'Historical Snapshot'}
                        </span>
                      </div>
                    </div>

                    {ver < activeVersionNum && (
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={handleRollback}
                        icon={<RotateCcw size={12} />}
                        disabled={isApplyingChange}
                        style={{ fontSize: '0.78rem', color: '#a78bfa' }}
                      >
                        Restore this version
                      </Button>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}"""

# Construct Code Studio Tab JSX
codestudio_tab_jsx = """{/* ================================================================= */}
        {/* TAB 3: Code Studio (Beginner Read-Only Code Viewer)               */}
        {/* ================================================================= */}
        {activeTab === 'code-studio' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem', height: '100%', maxWidth: '1240px', width: '100%', margin: '0 auto' }}>
            {/* Top Header */}
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                flexWrap: 'wrap',
                gap: '0.75rem',
                padding: '1rem 1.25rem',
                background: 'rgba(15, 20, 36, 0.85)',
                border: '1px solid rgba(255, 255, 255, 0.08)',
                borderRadius: '14px',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                <div style={{ padding: '0.45rem', borderRadius: '8px', background: 'rgba(6, 182, 212, 0.15)' }}>
                  <Code2 size={20} color="#06b6d4" />
                </div>
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <span style={{ fontSize: '1rem', fontWeight: 700, color: '#ffffff' }}>Code Studio</span>
                    <span style={{ fontSize: '0.68rem', padding: '0.15rem 0.45rem', borderRadius: '4px', background: 'rgba(6, 182, 212, 0.15)', color: '#22d3ee', fontWeight: 700 }}>
                      READ ONLY
                    </span>
                  </div>
                  <span style={{ fontSize: '0.78rem', color: '#94a3b8' }}>
                    {currentProject?.name} • File: <strong style={{ color: '#e2e8f0' }}>{selectedStudioPath}</strong>
                  </span>
                </div>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
                <Button
                  variant="primary"
                  onClick={() => handleDownloadZip(currentProject)}
                  icon={<Download size={14} />}
                  disabled={isDownloadingZip}
                  style={{ background: 'linear-gradient(135deg, #0ea5e9, #6366f1)', fontWeight: 650 }}
                >
                  {isDownloadingZip ? 'Preparing ZIP...' : 'Download Full Source Code (ZIP)'}
                </Button>

                <Button
                  variant="secondary"
                  onClick={() => {
                    if (currentProject) handleOpenInDeveloperMode(currentProject);
                    else switchMode('developer');
                  }}
                  icon={<ArrowRight size={14} />}
                  style={{ background: 'rgba(99, 102, 241, 0.12)', border: '1px solid rgba(99, 102, 241, 0.3)', color: '#c7d2fe' }}
                >
                  Switch to Developer Mode to Edit
                </Button>
              </div>
            </div>

            {/* Help Banner */}
            <div
              style={{
                padding: '0.85rem 1.25rem',
                background: 'rgba(99, 102, 241, 0.08)',
                border: '1px solid rgba(99, 102, 241, 0.25)',
                borderRadius: '12px',
                fontSize: '0.82rem',
                color: '#c7d2fe',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                flexWrap: 'wrap',
                gap: '0.5rem',
              }}
            >
              <span>
                💡 Curious how your app was built? Here is the actual production code synthesized by AI. You can download the complete ZIP package or switch to Developer Mode anytime to edit files directly.
              </span>
              <button
                type="button"
                onClick={() => {
                  if (currentProject) handleOpenInDeveloperMode(currentProject);
                  else switchMode('developer');
                }}
                style={{ background: 'transparent', border: 'none', color: '#818cf8', fontWeight: 700, cursor: 'pointer', fontSize: '0.82rem', textDecoration: 'underline' }}
              >
                Edit in Developer Mode →
              </button>
            </div>

            {/* Code Split View */}
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: '260px 1fr',
                gap: '1rem',
                minHeight: '520px',
                background: 'rgba(10, 14, 26, 0.95)',
                border: '1px solid rgba(255, 255, 255, 0.08)',
                borderRadius: '16px',
                overflow: 'hidden',
                boxShadow: '0 8px 30px rgba(0, 0, 0, 0.35)',
              }}
            >
              {/* File Tree Left Column */}
              <div
                style={{
                  background: 'rgba(13, 18, 31, 0.85)',
                  borderRight: '1px solid rgba(255, 255, 255, 0.08)',
                  padding: '1.25rem',
                  overflowY: 'auto',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '0.5rem',
                }}
              >
                <span style={{ fontSize: '0.72rem', fontWeight: 700, color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                  Project Files
                </span>

                {studioFiles.map((node) => (
                  <div key={node.id}>
                    {node.type === 'directory' ? (
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                        <span style={{ fontSize: '0.8rem', fontWeight: 650, color: '#94a3b8', display: 'flex', alignItems: 'center', gap: '0.35rem', padding: '0.25rem 0.4rem' }}>
                          📁 {node.name}
                        </span>
                        {node.children?.map((child) => (
                          <button
                            key={child.id}
                            type="button"
                            onClick={async () => {
                              setSelectedStudioPath(child.path);
                              if (currentProject?.id) {
                                try {
                                  const res = await codeStudioApi.getFileContent(currentProject.id, child.path);
                                  setStudioCodeContent(res.content || '');
                                } catch {
                                  setStudioCodeContent(getFallbackFileContent(child.path, currentProject?.name));
                                }
                              }
                            }}
                            style={{
                              display: 'flex',
                              alignItems: 'center',
                              gap: '0.45rem',
                              padding: '0.35rem 0.65rem 0.35rem 1.4rem',
                              borderRadius: '6px',
                              fontSize: '0.78rem',
                              background: selectedStudioPath === child.path ? 'rgba(99, 102, 241, 0.2)' : 'transparent',
                              color: selectedStudioPath === child.path ? '#ffffff' : '#cbd5e1',
                              border: selectedStudioPath === child.path ? '1px solid rgba(99, 102, 241, 0.35)' : '1px solid transparent',
                              cursor: 'pointer',
                              textAlign: 'left',
                              width: '100%',
                            }}
                          >
                            📄 {child.name}
                          </button>
                        ))}
                      </div>
                    ) : (
                      <button
                        type="button"
                        onClick={async () => {
                          setSelectedStudioPath(node.path);
                          if (currentProject?.id) {
                            try {
                              const res = await codeStudioApi.getFileContent(currentProject.id, node.path);
                              setStudioCodeContent(res.content || '');
                            } catch {
                              setStudioCodeContent(getFallbackFileContent(node.path, currentProject?.name));
                            }
                          }
                        }}
                        style={{
                          display: 'flex',
                          alignItems: 'center',
                          gap: '0.45rem',
                          padding: '0.35rem 0.65rem',
                          borderRadius: '6px',
                          fontSize: '0.78rem',
                          background: selectedStudioPath === node.path ? 'rgba(99, 102, 241, 0.2)' : 'transparent',
                          color: selectedStudioPath === node.path ? '#ffffff' : '#cbd5e1',
                          border: selectedStudioPath === node.path ? '1px solid rgba(99, 102, 241, 0.35)' : '1px solid transparent',
                          cursor: 'pointer',
                          textAlign: 'left',
                          width: '100%',
                        }}
                      >
                        📄 {node.name}
                      </button>
                    )}
                  </div>
                ))}
              </div>

              {/* Code Viewer Right Column */}
              <div style={{ display: 'flex', flexDirection: 'column', background: '#080c16', overflow: 'hidden' }}>
                <div
                  style={{
                    padding: '0.75rem 1.25rem',
                    background: 'rgba(255, 255, 255, 0.02)',
                    borderBottom: '1px solid rgba(255, 255, 255, 0.06)',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    fontSize: '0.75rem',
                    color: '#64748b',
                  }}
                >
                  <span>{selectedStudioPath}</span>
                  <span>{studioCodeContent.split('\\n').length} lines</span>
                </div>

                <div style={{ flex: 1, padding: '1.25rem', overflow: 'auto', fontFamily: 'var(--font-mono, "JetBrains Mono", monospace)', fontSize: '0.82rem', lineHeight: 1.6, color: '#f8fafc' }}>
                  {isStudioLoading ? (
                    <div style={{ padding: '2rem', textAlign: 'center', color: '#94a3b8' }}>Loading source file...</div>
                  ) : (
                    <pre style={{ margin: 0, whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
                      {studioCodeContent}
                    </pre>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}"""

# Construct AI Assistant Tab JSX
assistant_tab_jsx = """{/* ================================================================= */}
        {/* TAB 5: AI Development Assistant                                  */}
        {/* ================================================================= */}
        {activeTab === 'assistant' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem', maxWidth: '980px', width: '100%', margin: '0 auto' }}>
            {/* Assistant Header */}
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '1.5rem',
                background: 'linear-gradient(135deg, rgba(139, 92, 246, 0.18), rgba(15, 20, 36, 0.95))',
                border: '1px solid rgba(139, 92, 246, 0.35)',
                borderRadius: '18px',
                boxShadow: '0 8px 30px rgba(0, 0, 0, 0.35)',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.85rem' }}>
                <div style={{ padding: '0.55rem', borderRadius: '12px', background: 'rgba(139, 92, 246, 0.2)', border: '1px solid rgba(139, 92, 246, 0.4)' }}>
                  <Bot size={24} color="#c4b5fd" />
                </div>
                <div>
                  <h2 style={{ fontSize: '1.25rem', fontWeight: 700, margin: 0, color: '#ffffff' }}>
                    AI Development Assistant
                  </h2>
                  <span style={{ fontSize: '0.8rem', color: '#94a3b8' }}>
                    Project Context: <strong style={{ color: '#c4b5fd' }}>{currentProject?.name}</strong> • Version {activeVersionNum}.0
                  </span>
                </div>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={() => {
                    if (currentProject) handleLaunchProjectPreview(currentProject);
                    else setActiveTab('preview');
                  }}
                  icon={<Play size={13} />}
                  style={{ background: 'rgba(16, 185, 129, 0.15)', border: '1px solid rgba(16, 185, 129, 0.3)', color: '#34d399' }}
                >
                  View Live App
                </Button>
              </div>
            </div>

            {/* Context-Aware Natural Language App Refinement Panel */}
            <div
              data-testid="app-refinement-panel"
              style={{
                background: 'rgba(10, 14, 26, 0.95)',
                border: '1px solid rgba(139, 92, 246, 0.35)',
                borderRadius: '18px',
                padding: '1.75rem',
                display: 'flex',
                flexDirection: 'column',
                gap: '1.25rem',
                boxShadow: '0 8px 30px rgba(0, 0, 0, 0.4)',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderBottom: '1px solid rgba(255, 255, 255, 0.08)', paddingBottom: '0.85rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <Sparkles size={16} color="#c4b5fd" />
                  <span style={{ fontSize: '1.05rem', fontWeight: 700, color: '#ffffff' }}>
                    Refine “{currentProject?.name}”
                  </span>
                  <span style={{ fontSize: '0.72rem', fontWeight: 700, padding: '0.15rem 0.45rem', borderRadius: '4px', background: 'rgba(139, 92, 246, 0.2)', color: '#c4b5fd' }}>
                    v{activeVersionNum}
                  </span>
                </div>

                {activeVersionNum > 1 && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={handleRollback}
                    icon={<RotateCcw size={12} />}
                    disabled={isApplyingChange}
                    style={{ color: '#fca5a5', fontSize: '0.75rem' }}
                  >
                    Rollback to v{activeVersionNum - 1}
                  </Button>
                )}
              </div>

              {/* Suggested Quick Refinement Prompts */}
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.45rem' }}>
                {[
                  'Add dark mode toggle to the navigation bar',
                  'Add search bar filter for items',
                  'Change primary color theme to emerald',
                  'Add export to CSV capability',
                ].map((sug, i) => (
                  <button
                    key={i}
                    type="button"
                    onClick={() => handleSendRefinement(sug)}
                    disabled={isRefining || isApplyingChange}
                    style={{
                      background: 'rgba(139, 92, 246, 0.1)',
                      border: '1px solid rgba(139, 92, 246, 0.25)',
                      borderRadius: '9999px',
                      padding: '0.35rem 0.75rem',
                      color: '#c4b5fd',
                      fontSize: '0.75rem',
                      cursor: 'pointer',
                      transition: 'all 0.15s ease',
                    }}
                  >
                    + {sug}
                  </button>
                ))}
              </div>

              {/* Refinement Messages History */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem', maxHeight: '360px', overflowY: 'auto' }}>
                {refinementMessages.length === 0 ? (
                  <div style={{ padding: '2rem', textAlign: 'center', color: '#64748b', fontSize: '0.84rem' }}>
                    Describe any feature or modification in plain English, and the AI Assistant will update your running application.
                  </div>
                ) : (
                  refinementMessages.map((msg, i) => (
                    <div
                      key={i}
                      style={{
                        alignSelf: msg.role === 'user' ? 'flex-end' : 'flex-start',
                        maxWidth: '85%',
                        background: msg.role === 'user' ? 'rgba(99, 102, 241, 0.25)' : 'rgba(15, 20, 36, 0.85)',
                        border: msg.role === 'user' ? '1px solid rgba(99, 102, 241, 0.4)' : '1px solid rgba(255, 255, 255, 0.08)',
                        borderRadius: '12px',
                        padding: '0.75rem 1rem',
                        fontSize: '0.84rem',
                        color: '#f8fafc',
                      }}
                    >
                      {msg.content}
                    </div>
                  ))
                )}
              </div>

              {/* Action result confirmation */}
              {pendingActionResult && (
                <div
                  style={{
                    background: 'rgba(139, 92, 246, 0.12)',
                    border: '1px solid rgba(139, 92, 246, 0.35)',
                    borderRadius: '12px',
                    padding: '1rem',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '0.65rem',
                  }}
                >
                  <div style={{ fontWeight: 650, fontSize: '0.88rem', color: '#c4b5fd' }}>
                    {pendingActionResult.summary || 'Proposed changes ready for your approval:'}
                  </div>
                  <div style={{ display: 'flex', gap: '0.65rem' }}>
                    <Button
                      variant="primary"
                      size="sm"
                      onClick={() => handleConfirmRefinement(pendingActionResult.confirmation_token || '')}
                      disabled={isApplyingChange}
                      style={{ background: 'linear-gradient(135deg, #10b981, #06b6d4)', fontWeight: 650 }}
                    >
                      {isApplyingChange ? 'Applying...' : 'Approve & Apply to Live App'}
                    </Button>
                    <Button
                      variant="secondary"
                      size="sm"
                      onClick={() => setPendingActionResult(null)}
                      style={{ background: 'rgba(255, 255, 255, 0.06)' }}
                    >
                      Discard
                    </Button>
                  </div>
                </div>
              )}

              {/* Input box */}
              <div style={{ display: 'flex', gap: '0.65rem' }}>
                <input
                  type="text"
                  value={refinementPrompt}
                  onChange={(e) => setRefinementPrompt(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault();
                      handleSendRefinement();
                    }
                  }}
                  placeholder="e.g. Add an export CSV button, or toggle theme mode..."
                  style={{
                    flex: 1,
                    background: 'rgba(0, 0, 0, 0.3)',
                    border: '1px solid rgba(255, 255, 255, 0.12)',
                    borderRadius: '8px',
                    padding: '0.65rem 1rem',
                    color: '#ffffff',
                    fontSize: '0.84rem',
                    outline: 'none',
                  }}
                />
                <Button
                  variant="primary"
                  onClick={() => handleSendRefinement()}
                  disabled={!refinementPrompt.trim() || isRefining || isApplyingChange}
                  style={{ background: 'linear-gradient(135deg, #7c3aed, #6366f1)', fontWeight: 650 }}
                >
                  {isRefining ? 'Thinking...' : 'Refine with AI'}
                </Button>
              </div>
            </div>
          </div>
        )}"""

# Beginner Sidebar JSX
sidebar_jsx = """      <div
        className="beginner-workspace-container"
        style={{
          display: 'flex',
          flex: 1,
          width: '100%',
          minHeight: 'calc(100vh - 60px)',
          background: 'var(--bg-primary, #0a0d14)',
          position: 'relative',
        }}
      >
        {/* Dedicated 5-Option Beginner Mode Sidebar */}
        <aside
          className="beginner-mode-sidebar"
          role="navigation"
          aria-label="Beginner Mode Navigation"
          style={{
            width: '240px',
            flexShrink: 0,
            background: 'rgba(13, 18, 31, 0.95)',
            borderRight: '1px solid rgba(255, 255, 255, 0.08)',
            backdropFilter: 'blur(16px)',
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'space-between',
            padding: '1.25rem 0.85rem',
            zIndex: 10,
          }}
        >
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
            {/* Mode Badge */}
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem',
                padding: '0.45rem 0.75rem',
                background: 'rgba(139, 92, 246, 0.12)',
                border: '1px solid rgba(139, 92, 246, 0.3)',
                borderRadius: '10px',
              }}
            >
              <Sparkles size={15} color="#c4b5fd" />
              <div>
                <div style={{ fontSize: '0.72rem', fontWeight: 800, color: '#c4b5fd', letterSpacing: '0.04em' }}>BEGINNER MODE</div>
                <div style={{ fontSize: '0.65rem', color: '#94a3b8' }}>AI Application Workspace</div>
              </div>
            </div>

            {/* Dedicated 5 Nav Items */}
            <nav style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
              {[
                { id: 'projects', label: 'Projects', icon: <FolderKanban size={17} color="#818cf8" />, badge: undefined },
                { id: 'overview', label: 'Overview', icon: <Compass size={17} color="#38bdf8" />, badge: undefined },
                { id: 'code-studio', label: 'Code Studio', icon: <Code2 size={17} color="#06b6d4" />, badge: 'CODE' },
                { id: 'preview', label: 'Live Preview', icon: <Play size={17} color="#10b981" />, badge: 'LIVE' },
                { id: 'assistant', label: 'AI Assistant', icon: <Bot size={17} color="#a78bfa" />, badge: 'AI' },
              ].map((item) => (
                <button
                  key={item.id}
                  type="button"
                  onClick={() => {
                    setActiveTab(item.id as any);
                    if (item.id === 'preview' && currentProject) {
                      handleLaunchProjectPreview(currentProject);
                    }
                  }}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '0.6rem 0.85rem',
                    borderRadius: '8px',
                    fontSize: '0.84rem',
                    fontWeight: activeTab === item.id ? 700 : 500,
                    background: activeTab === item.id ? 'rgba(99, 102, 241, 0.18)' : 'transparent',
                    color: activeTab === item.id ? '#ffffff' : '#94a3b8',
                    border: activeTab === item.id ? '1px solid rgba(99, 102, 241, 0.35)' : '1px solid transparent',
                    cursor: 'pointer',
                    transition: 'all 0.15s ease',
                    textAlign: 'left',
                    width: '100%',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
                    {item.icon}
                    <span>{item.label}</span>
                  </div>
                  {item.badge && (
                    <span
                      style={{
                        fontSize: '0.62rem',
                        fontWeight: 700,
                        padding: '0.12rem 0.45rem',
                        borderRadius: '4px',
                        background: item.badge === 'LIVE' ? 'rgba(16, 185, 129, 0.2)' : 'rgba(99, 102, 241, 0.2)',
                        color: item.badge === 'LIVE' ? '#34d399' : '#818cf8',
                        border: `1px solid ${item.badge === 'LIVE' ? 'rgba(16, 185, 129, 0.35)' : 'rgba(99, 102, 241, 0.35)'}`,
                      }}
                    >
                      {item.badge}
                    </span>
                  )}
                </button>
              ))}
            </nav>
          </div>

          {/* Switch to Developer Mode Card */}
          <div
            style={{
              padding: '0.85rem',
              borderRadius: '10px',
              background: 'rgba(255, 255, 255, 0.03)',
              border: '1px solid rgba(255, 255, 255, 0.06)',
              display: 'flex',
              flexDirection: 'column',
              gap: '0.65rem',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.45rem' }}>
              <Code2 size={14} color="#818cf8" />
              <span style={{ fontSize: '0.72rem', fontWeight: 600, color: '#e2e8f0' }}>Developer Studio</span>
            </div>
            <p style={{ fontSize: '0.66rem', color: '#64748b', margin: 0, lineHeight: 1.4 }}>
              Monaco code editor, terminal, and all 14 engineering tools.
            </p>
            <button
              type="button"
              onClick={() => {
                if (currentProject && onNavigateToProjectInDev) {
                  onNavigateToProjectInDev(currentProject);
                } else {
                  switchMode('developer');
                }
              }}
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '0.4rem',
                padding: '0.45rem 0.65rem',
                borderRadius: '6px',
                background: 'linear-gradient(135deg, rgba(79, 70, 229, 0.95), rgba(6, 182, 212, 0.95))',
                color: '#ffffff',
                fontSize: '0.72rem',
                fontWeight: 700,
                border: 'none',
                cursor: 'pointer',
                boxShadow: '0 2px 8px rgba(79, 70, 229, 0.35)',
              }}
            >
              <span>Developer Mode</span>
              <ArrowRight size={12} />
            </button>
          </div>
        </aside>

        {/* Main Content Viewport */}
        <main
          style={{
            flex: 1,
            minWidth: 0,
            overflowY: 'auto',
            padding: '2.5rem 1.5rem',
            display: 'flex',
            flexDirection: 'column',
            gap: '2.5rem',
          }}
        >"""

# Assemble new body:
# On Tab 1: projects
tab_projects_jsx = f"""        {{/* ================================================================= */}}
        {{/* TAB 1: Projects Gallery & Creation Hub                           */}}
        {{/* ================================================================= */}}
        {{activeTab === 'projects' && (
          <>
            {stepper_block}

            {hero_block}

            {blueprint_block}

            {gallery_block}

            {learn_block}
          </>
        )}}"""

# On Tab 4: preview
tab_preview_jsx = f"""        {{/* ================================================================= */}}
        {{/* TAB 4: Live Application Preview Frame & Quick Refinement         */}}
        {{/* ================================================================= */}}
        {{activeTab === 'preview' && (
          {live_block}
        )}}"""

new_main_content = f"""{sidebar_jsx}
{tab_projects_jsx}

{overview_tab_jsx}

{codestudio_tab_jsx}

{tab_preview_jsx}

{assistant_tab_jsx}
        </main>
      </div>"""

# Replace in text: from '<main' (around line 1102) to '</main>\n    </div>'
head_part = text[:idx_stepper].rsplit('<main', 1)[0]
tail_part = text[idx_main_close:]

updated_text = head_part + new_main_content + "\n    </div>\n  );\n};\n"

with open('frontend/src/views/UserModeWorkspace.tsx', 'w', encoding='utf-8') as f:
    f.write(updated_text)

print("UserModeWorkspace.tsx rewritten successfully with 5 tabs!")
