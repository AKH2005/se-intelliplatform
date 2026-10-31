# Script to structure UserModeWorkspace.tsx into the 5-tab dedicated Beginner Mode shell

with open('frontend/src/views/UserModeWorkspace.tsx', 'r', encoding='utf-8') as f:
    text = f.read()

# Make sure handleLaunchProjectPreview sets activeTab = 'preview'
old_launch = """  const handleLaunchProjectPreview = async (proj: ProjectResponse) => {
    selectProject(proj);
    setCreatedProject(proj);
    setBuilderStage('LAUNCHING_CONTAINER');"""

new_launch = """  const handleLaunchProjectPreview = async (proj: ProjectResponse) => {
    selectProject(proj);
    setCreatedProject(proj);
    setActiveTab('preview');
    setBuilderStage('LAUNCHING_CONTAINER');"""

if old_launch in text:
    text = text.replace(old_launch, new_launch, 1)
    print("handleLaunchProjectPreview updated to set activeTab = 'preview'.")

# Also in executeAutonomousBuild, ensure setActiveTab('preview')
old_auto_live = """      setBuilderStage('LIVE');
      setStageProgressText('Application is running live in isolated Docker container!');"""

new_auto_live = """      setBuilderStage('LIVE');
      setActiveTab('preview');
      setStageProgressText('Application is running live in isolated Docker container!');"""

if old_auto_live in text:
    text = text.replace(old_auto_live, new_auto_live, 1)
    print("executeAutonomousBuild updated to set activeTab = 'preview'.")

with open('frontend/src/views/UserModeWorkspace.tsx', 'w', encoding='utf-8') as f:
    f.write(text)
print("Updated UserModeWorkspace.tsx handlers.")

