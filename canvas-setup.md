# Canvas Setup Guide: AI Ethics Under Pressure Simulation

## Prerequisites
- Deployed simulation on Railway (or similar hosting)
- Admin token configured
- Padlet board created
- 30-50 minutes class time

## Step 1: Create Module Structure

1. **Create New Module**
   - Modules → "+ Module"
   - Name: "AI Ethics Crisis Simulation"
   - Lock until: [Your class date]

2. **Add Module Items**
   - Page: "Simulation Instructions"
   - Page: "Team Assignments"
   - External Tool: "Crisis Dashboard"
   - Assignment: "Ethics Reflection Paper"

## Step 2: Create Instruction Page

**Page Title:** "AI Ethics Simulation Instructions"

```html
<h2>Mission Briefing</h2>
<p>You are members of your nation's AI Advisory Council. The year is 2026.
AGI is 18 months away. Your decisions will shape humanity's future.</p>

<h3>Your Objectives:</h3>
<ul>
  <li>Navigate ethical dilemmas under time pressure</li>
  <li>Document decisions on the shared board</li>
  <li>Balance safety with competitive advantage</li>
</ul>

<h3>Rules:</h3>
<ol>
  <li>2 minutes per crisis - decide quickly</li>
  <li>All decisions are public to other teams</li>
  <li>Post your reasoning to Padlet</li>
  <li>No collaboration between teams</li>
</ol>
```

## Step 3: Create Team Dashboard Page

**Page Title:** "Crisis Command Center"

```html
<style>
  .team-section {
    margin: 20px 0;
    padding: 20px;
    border: 2px solid #ccc;
    border-radius: 10px;
  }
  .team-usa { border-color: #3b82f6; }
  .team-china { border-color: #ef4444; }
  .team-neutral { border-color: #f59e0b; }
</style>

<div class="team-section team-usa">
  <h2>🇺🇸 Team USA - Democratic Oversight Model</h2>
  <iframe src="https://YOUR-APP.railway.app/dashboard/usa"
          width="100%" height="600px" frameborder="0">
  </iframe>
</div>

<div class="team-section team-china">
  <h2>🇨🇳 Team China - State-Guided Model</h2>
  <iframe src="https://YOUR-APP.railway.app/dashboard/china"
          width="100%" height="600px" frameborder="0">
  </iframe>
</div>

<div class="team-section team-neutral">
  <h2>🌐 Team Neutral - Open Governance Model</h2>
  <iframe src="https://YOUR-APP.railway.app/dashboard/neutral"
          width="100%" height="600px" frameborder="0">
  </iframe>
</div>
```

## Step 4: Create Instructor Admin Page (Unpublished)

**Page Title:** "Instructor Control Panel" *(Set to Unpublished)*

```
Admin Dashboard: https://YOUR-APP.railway.app/admin?token=YOUR_TOKEN

Crisis Controls:
- Inject specific crises to teams
- Control countdown timer
- Advance timeline
- Monitor all teams

News Ticker: https://YOUR-APP.railway.app/news_ticker
```

## Step 5: Embed Decision Board

**Option A: Embed Padlet**
```html
<div class="padlet-embed" style="border:1px solid rgba(0,0,0,0.1);
     border-radius:2px;box-sizing:border-box;overflow:hidden;
     position:relative;width:100%;background:#F4F4F4">
  <iframe src="https://padlet.com/embed/YOUR_PADLET_ID"
          frameborder="0" style="width:100%;height:600px;">
  </iframe>
</div>
```

**Option B: Link to Padlet**
```html
<a href="https://padlet.com/YOUR_PADLET" target="_blank"
   class="btn btn-primary">
  Open Decision Board in New Tab
</a>
```

## Step 6: Create Reflection Assignment

**Assignment Settings:**
- Title: "AI Ethics Simulation Reflection"
- Points: 30
- Submission Type: Online - Text Entry
- Due: End of class + 24 hours

**Instructions:**
```
Reflect on your experience in the AI Ethics simulation:

1. Which crisis was most challenging? Why? (5 points)
2. When did you first compromise your ethical principles? (5 points)
3. How did seeing other teams' decisions influence you? (5 points)
4. What surprised you about your own choices? (5 points)
5. How might this experience inform real AI governance? (10 points)

Minimum 500 words. Reference specific crises and decisions.
```

## Step 7: Pre-Class Checklist

- [ ] Test all iframes load properly
- [ ] Verify admin dashboard access
- [ ] Clear Padlet of previous posts
- [ ] Test one crisis injection
- [ ] Prepare team assignments
- [ ] Have backup plan if tech fails

## Step 8: Running the Session

1. **Pre-Brief (5 min)**
   - Assign teams randomly
   - Open instruction page
   - Emphasize time pressure

2. **Active Phase (30 min)**
   - Start with minor crisis
   - Escalate every 5-10 minutes
   - Monitor Padlet for decisions
   - Inject targeted crises based on choices

3. **Debrief (15 min)**
   - Reveal AI model differences
   - Review decision patterns
   - Discuss ethical drift

## Troubleshooting

**Iframe won't load:**
- Check Railway app is running
- Verify HTTPS certificate
- Try opening in new tab

**Students can't see crisis:**
- Manually inject via admin panel
- Check active crisis status
- Refresh team dashboard

**Padlet issues:**
- Ensure public write permissions
- Check post moderation settings
- Have backup Google Doc ready

## Grading Rubric

| Component | Points | Criteria |
|-----------|--------|----------|
| Participation | 10 | Responded to all crises |
| Decision Quality | 10 | Thoughtful justifications |
| Reflection Paper | 10 | Depth of analysis |
| **Total** | **30** | |

## Tips for Success

- Run a practice session alone first
- Have co-instructor monitor admin panel
- Screenshot interesting decisions
- Save Padlet posts before clearing
- Consider recording session for research
