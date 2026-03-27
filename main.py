import json
import os

import anthropic
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from rag import get_project, search_similar, seed_from_dataset
from story_chunker import chunk_transcript

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MODEL = "claude-haiku-4-5-20251001"

_GUIDE = """
**EO**

**MASTER STORYTELLING GUIDE**

*The editorial principles, narrative frameworks, and production standards*

*that define world-class storytelling at EO.*

Version 1.0  |  2026

EO Studio  |  Internal Document | Gunwook Yoo

# **TABLE OF CONTENTS**

**PART 1 — The EO Standard** 1.1 What Makes EO Different 1.2 The Non-Negotiables 1.3 Why Audience Selection Is the Foundation 1.4 The Competitive Benchmark

**PART 2 — Narrative Architecture** 2.1 Journey Narrative vs. Situation Narrative 2.2 The Five Structural Principles 2.3 Quick-Reference Decision Guide

**PART 3 — The Interview** 3.1 EO Interview Fundamentals 3.2 The Pre-Production One-Pager 3.3 Interview Technique

**PART 4 — Editorial Judgment** 4.1 Summary vs. Direction 4.2 Chapter Design 4.3 The Efficiency-Quality Balance

**PART 5 — The First 30 Seconds** 5.1 The Intro Formula 5.2 Opening Patterns That Work

**PART 6 — Thumbnail & Title** 6.1 The Thumbnail Copy Formula 6.2 Title Design 6.3 Protecting the Interviewee

**PART 7 — AI-Powered 10x Production** 7.1 Where AI Fits in the EO Workflow 7.2 What AI Cannot Replace

**PART 8 — Production Workflow** 8.1 The EO Pipeline 8.2 Quality Checklist & Strategic Alignment

**PART 9 — Learning From the Best** 9.1 Acquired 9.2 Diary of a CEO 9.3 Lex Fridman 9.4 Synthesis: What EO Takes Forward

**PART 10 — Onboarding & Common Pitfalls** 10.1 New Team Member Path 10.2 Content PD Growth Path 10.3 The 12 Most Common Pitfalls 10.4 The Feedback Process

# **PART 1: THE EO STANDARD**

EO is not a YouTube channel. EO is a global media studio covering the startup and venture ecosystem — through in-depth interviews and documentaries with founders, investors, and technology leaders. The benchmark is not other YouTube creators. The benchmark is 20VC, CNBC Make It, Bloomberg Originals, and First Round Review.

This guide exists because EO's editorial standards cannot live in one person's head. Every decision — what to cut, how to frame a thumbnail, when to push an interviewee — should trace back to a clear principle. What follows is the accumulated editorial judgment of four years, distilled into something a new team member can study, internalize, and apply.

## **1.1 What Makes EO Different**

Three things separate EO from the rest of startup media:

1. **Storytelling over Q&A.** Most startup interviews arrange questions in sequence and let the guest talk. EO treats every interview as raw material for narrative construction. The editor's job is not transcription — it is authorship.

2. **Global perspective, local depth.** EO covers the global startup ecosystem with a US-first lens. The audience is in San Francisco, New York, London, and Singapore. Every editorial decision starts with: "Does this matter to a global audience?"

3. **The editorial layer.** EO adds context that the interviewee cannot. Age, funding stage, market timing, competitive landscape — these surrounding facts transform a talking head into a story worth watching.

## **1.2 The Non-Negotiables**

Five Rules That Never Bend:
1. Every video must have an editorial perspective. If you can't articulate what your angle is in one sentence, you're not ready to edit.
2. The audience test comes first. Before any other feedback: "Would someone in the US startup ecosystem find this worth 15 minutes of their time?"
3. An editing direction is not a summary. A summary describes what exists. An editing direction argues for what to keep and what to cut. If your document doesn't say what to remove, it's not an editing direction.
4. Protect the interviewee's business interests. Never frame a story in a way that damages your subject's relationships with customers, investors, or partners.
5. Show, don't describe. Product features are shown on screen. Credentials are text overlays. Background context is B-roll. The voice track carries only insight and narrative.

## **1.3 Why Audience Selection Is the Foundation**

TY articulates a principle that governs every strategic decision at EO: not all views are created equal. A video can generate 15 million views and still fail as a business — if the audience it attracts has no commercial value to advertisers or sponsors.

The '1 ≠ 1' Principle — From TY:
Core insight: "The value of a single view is not the same across all content. One view from a startup founder considering a $50K SaaS purchase is worth more than a thousand views from someone watching for casual entertainment."
The proof: before EO, a dating and sexuality content series generated 15 million views, yet attracted zero advertiser interest. The audience was massive but commercially unmarketable. Meanwhile, content about disability mobility rights drew a smaller but deeply engaged audience with clearly identifiable sponsors.
The EO application: This is why EO targets the global startup and venture ecosystem. The audience is smaller, but each viewer is a decision-maker: a founder evaluating tools, an investor seeking deal flow, a tech professional choosing their next career move. Media is not an attention business — it is an audience value maximization business.

Viral ≠ Monetizable: If a content concept could generate massive views but attract an audience with no purchasing power, no professional identity, and no advertiser appeal — it is not an EO concept. Scale without audience value is a trap. Every content decision at EO starts with: "Who is this for, and why would someone pay to reach them?"

## **1.4 The Competitive Benchmark**

To operate at EO's level, you need to know what world-class looks like:
- 20VC (Harry Stebbings): Speed, access, and volume in VC content. Match the access level; exceed the narrative depth.
- CNBC Make It: Making business stories feel human and accessible. Adopt the clarity; add more intellectual rigor.
- Acquired (Ben & David): Research depth — 300+ hours per episode. We can't match the hours, but we can match the principle: depth is the differentiator.
- Diary of a CEO (Bartlett): Data-driven packaging and systematic testing. Adopt the thumbnail/title testing rigor.
- Bloomberg Originals: Production quality and visual storytelling. The visual standard to aim for in B-roll and graphics.

# **PART 2: NARRATIVE ARCHITECTURE**

This is the most important section in this guide. Every other skill — thumbnails, titles, hooks, production — is downstream of your ability to choose and execute the right narrative structure.

## **2.1 The Core Decision: Journey vs. Situation**

EO does not use one template for all interviews. The narrative structure is selected based on the interviewee's achievement scale and story characteristics. This is not optional — it is the foundation of every editorial decision that follows.

Journey Narrative:
- When to use: The subject has achieved at massive scale ($1B+, industry-defining). Their path from A to Z is inherently compelling at every stage.
- Structure: Follow the chronological or thematic arc of how they built something extraordinary. Each chapter is a phase of the journey.
- The test: "Is every stage of this person's journey genuinely interesting?" If yes → journey.
- Risk if misapplied: If used for early-stage subjects: the video feels thin, padding out a story that hasn't happened yet.

Situation Narrative:
- When to use: The subject is earlier-stage ($10M or below, still proving). Their full biography isn't yet interesting enough to sustain a 20-minute video.
- Structure: Center on one specific moment, insight, or situation that only this person can speak to right now. Don't follow their whole life.
- The test: "What is the one thing this person knows that nobody else is saying?" Build around that single insight.
- Risk if misapplied: If used for massive-scale subjects: you waste the most compelling material by constraining the scope.

The Most Common Mistake at EO: Applying hero's journey to everyone. A 24-year-old with a $5M seed round does not need a childhood-to-present narrative arc. That format works when the journey has enough scale at every stage to hold attention. For earlier subjects, find the one extraordinary thing about their current moment and build the entire video around it.

## **2.2 How the World's Best Storytellers Choose Structure**

### **Principle 1: Let the Scale of Achievement Dictate the Scope**

This is EO's first rule. The bigger the story, the wider the lens. The smaller the story, the tighter the focus.

- Acquired (Ben Gilbert & David Rosenthal): Their multi-hour episodes on Nike, NVIDIA, or Berkshire Hathaway work because the companies' histories are genuinely fascinating at every decade. They would never do a 4-hour episode on a Series A startup — the material wouldn't sustain it.
- Ken Burns: Burns uses the same instinct in documentary. A 10-part series on the Civil War works because the scope of events justifies the duration. His shorter films have tighter framing — not less quality, but less span.

EO Application: Before you start editing, ask: "How much timeline does this person's story actually earn?" A 10-year journey building a $10B company earns a full journey arc. A 2-year journey to a $3M ARR product earns a tight situation frame. Let the material tell you the structure — don't impose one.

### **Principle 2: Create Tension Through Information Asymmetry**

The audience stays when they know something the story hasn't resolved yet — or when they're missing information they desperately want.

- Ira Glass (This American Life): Glass's formula — anecdote + reflection, alternating — works because the anecdote raises a question and the reflection provides (or delays) the answer. The audience is always in a state of mild suspense.
- Steven Bartlett (DOAC): Bartlett sequences questions to lead guests into territory they haven't explored publicly. The tension comes from unpredictability: the audience doesn't know what the guest will say because the guest doesn't know either.
- Howard Stern: Stern creates tension by asking the question everyone is thinking but nobody says out loud. The audience's anticipation of the guest's reaction IS the hook.

EO Application: Every chapter of an EO video should create a question in the viewer's mind that the next chapter answers. If chapter 3 doesn't make the viewer need chapter 4, the structure is broken. Map your chapters as a chain of questions, not a list of topics.

### **Principle 3: Separate What's Shown From What's Told**

The most sophisticated storytellers use multiple layers — what the subject says, what the editor shows, and what the audience infers from the gap between them.

- Errol Morris: Morris lets subjects speak while showing contradicting or contextualizing visuals. The audience does the interpretive work. This creates engagement that pure dialogue cannot.
- Alex Gibney: Gibney's documentaries build a case through accumulation. Each piece of evidence seems small alone, but the editorial sequencing creates an argument the audience assembles themselves.

EO Application: When an interviewee talks about their product, don't let the audio carry the explanation alone. Show the product. When they claim rapid growth, show the numbers on screen. When they describe a pivotal moment, use B-roll that puts the audience in that context. The voice track carries insight. Everything else carries evidence.

### **Principle 4: Preparation Depth Is the Invisible Differentiator**

The audience can't see the research, but they can feel it. When an interviewer knows more than the guest expects, the conversation goes places the guest didn't plan.

- Lex Fridman: For some guests, Fridman prepares for years. He reads their entire body of work and builds a relationship before recording. The result: guests say things they've never said publicly, because they feel intellectually safe.
- Terry Gross (Fresh Air): Gross finds the one detail in a guest's history that everyone else missed. That single unexpected question opens a door the guest didn't expect to walk through.

EO Application: For every EO interview, the producer should know at least three things about the subject that the subject doesn't expect us to know. This isn't about gotcha journalism — it's about demonstrating respect. When a founder realizes you've done the work, they give you the real answers, not the media-trained ones.

### **Principle 5: Control the Emotional Rhythm**

Great stories are not uniformly intense. They breathe — tension, release, tension, release — in patterns that keep the audience engaged without exhausting them.

- David Attenborough: Attenborough alternates between awe (wide shots, dramatic reveals) and intimacy (close-ups, quiet narration). The rhythm prevents both boredom and fatigue.
- Robert Caro: Caro's books alternate between sweeping historical context and intensely personal scenes. The scale changes create a breathing pattern that sustains 600+ pages.

EO Application: Map the emotional intensity of each chapter before you finalize the edit. If three intense chapters appear in sequence, the audience will disengage. Insert a quieter chapter — context, reflection, a lighter moment — to let them breathe before the next peak.

## **2.3 Narrative Structure Quick-Reference**

- Subject has $1B+ outcome, 10+ year journey → Journey narrative. Map the 4-6 most pivotal moments. Each becomes a chapter.
- Subject is early-stage, one breakout insight → Situation narrative. Identify the single strongest insight. Build everything around it.
- Subject has massive scale but one defining decision → Hybrid: situation within journey. Frame around the decision, use journey as context before and after.
- Subject's journey is interesting only at certain stages → Selective journey. Skip the uninteresting stages entirely. Cover only the 2-3 moments with real narrative weight.
- Multiple subjects, one theme → Thematic narrative. The theme is the protagonist, not any individual. Each subject illuminates one facet.

# **PART 3: THE INTERVIEW**

TY on the Interviewer's Role: "An interviewer is not someone who asks what they are personally curious about. An interviewer is someone who asks what the audience is curious about — and translates the answer into language the public can understand. The moment you start satisfying your own curiosity instead of the viewer's, you've stopped being a media professional and become a fan." — TY, CEO&Founder, EO

EO interviews operate in a specific context: the startup and venture ecosystem. This means every interview carries business implications. The subject has investors, customers, competitors, and employees who will watch. The interviewer's job is to extract maximum insight while respecting these realities.

## **3.1 EO Interview Fundamentals**

Before any technique, these principles govern every EO interview:

1. **Know their business interests.** Before you sit down, understand who their customers are, who their investors are, and what narrative they need to protect. A founder whose customers are law firms cannot be framed as "replacing lawyers" — even if that's technically what their product does. Framing matters.

2. **Earn the real answer.** Every founder has a media-trained version and a real version. The media-trained version is polished, safe, and boring. Your job is to make them feel safe enough to give you the real version. This requires preparation — when they realize you've done the work, they stop performing.

3. **The US audience test.** Before, during, and after every interview: "Would a founder, investor, or tech professional in the US find this valuable?" If the answer is no, you're off track. This is not about dumbing down — it's about relevance. Global audience, global standards.

4. **Push without damaging.** EO pushes interviewees into uncomfortable territory — that's where the best content lives. But there's a line between productive discomfort and content that harms their business relationships. Learn where that line is for each subject.

## **3.2 The Pre-Production One-Pager**

Before any interview goes into production, the producer creates a one-pager — a single document that forces clarity on three questions:
- Audience Definition: Who exactly is this for? ("Series A founders in SaaS evaluating whether to expand to enterprise sales" — not "startup people")
- Content Plan: What will the viewer learn or feel? A specific thesis: "This video argues that [X] — and proves it through [Y]"
- Feedback Checkpoint: How will we know if the plan is working?

One-Pager Non-Negotiable: If you cannot fill out this one-pager convincingly, the interview is not ready for production. A great interviewee with a vague plan produces mediocre content. A clear plan with an average interviewee produces content worth watching. The plan is the product — the interview is the raw material.

## **3.3 Interview Technique: The EO Approach**

### **Pre-Interview: Build the Advantage**

- **Research the gaps.** Watch every previous interview your subject has done. Note what they always say and what they've never been asked. Your questions should target the unexplored territory — that's where original content lives.
- **Identify the 3 surprises.** Know at least three things about the subject that they don't expect you to know. A specific data point from their early days. A quote from a former colleague. A market trend that contextualizes their business. These aren't gotchas — they're signals that you've earned their respect.
- **Map the emotional architecture.** Before you start, know where you want the emotional peaks and valleys. Which topic will create tension? Which will create warmth? Which is the moment you'll use for the intro hook?

### **During: Extract, Don't Interrogate**

- **Use silence as a tool.** When a guest finishes an answer, wait. Count to five in your head. In that silence, they often move past their prepared response and into genuine reflection. Lex Fridman sustains 21-second silences. You don't need to go that far, but 5 seconds of comfortable silence will give you material that a rapid follow-up never will.
- **Steelman before you challenge.** Before pushing back on any claim, articulate the strongest version of their argument first. "So what you're saying is [strongest version] — but here's what I'm wondering..." This creates intellectual safety. They know you're not trying to trap them, so they're willing to explore uncertainty with you.
- **Follow the energy, not the script.** Your prep gives you a map, not a railroad. When the subject lights up about something unexpected, follow it. The best moments in EO interviews come from departures, not from the plan.
- **Ask the question everyone's thinking.** Howard Stern's greatest skill is asking what the audience wants to know but wouldn't dare ask. In startup interviews, this is often about failure, money, or the gap between the public narrative and reality. Ask it — respectfully, but ask it.

### **Post-Interview: Find the Gold**

- **The killer quote hunt.** In every interview, there is one sentence that could be a title, a thumbnail, or an intro hook. It usually comes when the subject stops performing and starts thinking out loud. Find that sentence before you start editing.
- **Mark the 'never said this before' moments.** These are your most valuable assets. When a subject says something genuinely new — not recycled from previous interviews — flag it immediately. This is what makes an EO video unique.
- **Note the contradictions.** When a subject says one thing early and something slightly different later, that's not a mistake — it's where the real story lives. The gap between their prepared narrative and their unguarded thoughts is your editorial territory.

# **PART 4: EDITORIAL JUDGMENT**

Editing is not arranging information in order. Editing is making an argument about what matters. If your editorial document doesn't say what to cut, you haven't started editing yet.

## **4.1 Editing Direction vs. Interview Summary**

Interview Summary vs. Editing Direction:
- Purpose: Summary describes what exists in the raw footage. Direction argues for what the final video should contain.
- Key question: Summary asks "What did the subject say?" Direction asks "What story should we tell, and what do we cut to tell it?"
- Tells you: Summary = the topics covered. Direction = the angle, the structure, and the deletions.
- Example summary: "In the interview, the founder discussed their childhood, education, first startup, pivot, and current product."
- Example direction: "Lead with the pivot story (timestamp 34:00). Cut the childhood section entirely — it doesn't serve the audience. The thumbnail hook is the $50M rejection at 23:15."

## **4.2 The Chapter Design Rules**

Every chapter in an EO video must follow these constraints:

1. **One question per chapter.** If a chapter tries to answer two questions, split it. The audience should always know what this chapter is about.
2. **Chain of curiosity.** The end of each chapter should create a question that the next chapter answers. If chapter 3 doesn't make the viewer need chapter 4, you have a structural problem.
3. **Earn your minutes.** Every minute of screen time must justify itself. If a section could be a 3-second text overlay instead of a 2-minute verbal explanation, use the text overlay.
4. **Resume items are not story.** "She graduated from Stanford, worked at McKinsey, then joined Google" — that's a LinkedIn profile, not a narrative. Handle credentials as text overlays (3 seconds max) or cut them entirely.

## **4.3 Balancing Efficiency and Quality**

EO does not treat efficiency and quality as opposites. Both matter.
- Maximum craft: Marquee interviews, flagship content, series openers. Multiple editing passes, extensive B-roll, custom graphics, full thumbnail testing cycle.
- High quality, high velocity: Regular weekly content. Solid narrative structure, clean edit, tested thumbnail, efficient turnaround.
- Fast and functional: Time-sensitive content, breaking news, supplementary clips. Good enough structure, clean audio, basic graphics, rapid publish.

The EO Efficiency Principle: Efficiency is not the enemy of quality — wasted effort is. Spending 4 hours perfecting a transition that nobody will notice is not craftsmanship; it's misallocation. Spending 4 hours finding the perfect intro hook is not slow; it's investment in the thing that determines whether anyone watches at all. Know where the leverage is.

## **4.4 Content Processing**

Raw interview footage is not content. It is raw material. The editor's job is to process it:
- **Don't arrange — reconstruct.** Taking the interviewee's statements and putting them in chronological order is organizing, not editing. Editing means adding the surrounding context — age, funding stage, market conditions, competitor moves — that transforms a quote into a story.
- **Information the subject can't provide.** The interviewee tells you what happened to them. Your job is to add what was happening around them. A founder saying "we raised $5M" becomes a different story when the audience knows it happened in 2008, during the financial crisis, when VCs weren't writing checks.
- **The density test.** Watch any 60-second segment of your edit. Is every second earning its place? If you can remove 10 seconds without losing meaning, those 10 seconds should never have been there.

# **PART 5: THE FIRST 30 SECONDS**

The intro is where most EO videos are won or lost. The thumbnail gets the click. The intro determines whether they stay. You have 30 seconds to prove this video is worth the viewer's time.

## **5.1 The Three-Beat Intro**

EO uses a three-beat structure for intros. Each beat has a specific job:
1. Opening Hook (5-8 sec): A direct quote from the interviewee that is either surprising, counterintuitive, or stakes-setting. Example: "I turned down $200 million at 26 because I knew it was worth ten times that."
2. Number Punch (5-10 sec): Hard data that proves the scale of what you're about to watch. Example: "That company is now worth $4.2 billion, with zero venture capital."
3. The Closer (5-10 sec): A philosophical claim or provocative statement that frames the entire video. Example: "This is the story of how one founder proved that the entire VC model is broken."

## **5.2 The Thumbnail-Intro Contract**

The thumbnail and title make a promise. The intro must deliver on that promise — or deliberately subvert it to create even more curiosity.

Two Valid Strategies:
- Strategy A — Deliver immediately: If the thumbnail says "23-year-old built $1B company," the intro should start with that person explaining how it happened. No preamble, no background — straight to the payoff.
- Strategy B — Create a gap: If the thumbnail promises a success story, the intro can start with a moment of failure or doubt that makes the success feel impossible. "Two years ago, she couldn't make rent. Today, her company just IPO'd." The gap between the intro and the thumbnail promise creates tension.

## **5.3 Finding the Hook**

The hook usually isn't where you expect it. It's almost never in the first 10 minutes of the interview. Here's how to find it:
- **Scan for emotional intensity.** The best hook is the moment the subject's voice changes — when they stop reciting and start feeling. This often happens 30-45 minutes in, when their guard is down.
- **Look for the number that doesn't make sense.** "We went from 3 users to 300,000 in six weeks" — any data point that seems impossible or contradictory is a potential hook.
- **Find the contradiction.** "I was a college dropout building software for Harvard professors" — when the subject's identity and their achievement seem incompatible, that gap IS the hook.

## **5.4 Retention Architecture**

- **The 30-second cliff.** If viewers don't feel committed within 30 seconds, most leave. This is why the three-beat structure exists — it packs a complete narrative promise into half a minute.
- **Pattern interrupts every 2-3 minutes.** The audience's attention needs regular micro-refreshes: a visual change, a new speaker, a surprising data point, a tonal shift.
- **The 70% rule.** Viewers who make it past 70% of the video will almost always finish. Design your strongest content for the first third and the final third. The middle is where you sustain, not where you peak.

# **PART 6: THUMBNAIL & TITLE**

The thumbnail and title are not marketing — they are editorial decisions. They determine who clicks, what they expect, and whether the content delivers on the promise.

## **6.1 The EO Thumbnail Copy Formula**

The Formula: Age (or Time) × Achievement Scale = Gap
The thumbnail copy creates a click by juxtaposing two numbers that seem incompatible. The viewer's brain needs to resolve the gap — and the only way to resolve it is to click.
Examples: "23 → $1B" | "$0 to $50M in 18 months" | "Rejected 47 times → IPO" | "College dropout → $4B exit"
The gap between the two numbers is the click. If there's no gap, there's no click. If the gap isn't visible in the thumbnail, it doesn't exist.

## **6.2 Thumbnail vs. Title: Different Jobs**

- Thumbnail answers: "Why should I click?" — creates the gap that demands resolution. Optimize for visual clarity at mobile size, emotional expression, number contrast.
- Title answers: "What will I learn?" — previews the payoff. Optimize for specific promise, active verbs, no clickbait that the video can't deliver.

The Most Important Rule: Never promise something in the thumbnail/title that the video doesn't deliver in the first 30 seconds. Clickbait that doesn't pay off destroys trust — and YouTube's algorithm punishes it through low average view duration.

## **6.3 World-Class Packaging Systems**

Steven Bartlett's Testing Machine:
- 100+ thumbnail concepts per episode. Not 5-10. Over 100 are generated, narrowed through internal review, and the top candidates are tested with a panel of 1,000 viewers using eye-tracking technology.
- Environmental controls during testing. Bartlett's team monitors CO2 levels in viewing rooms — cognitive performance drops above 1000 ppm.
- EO takeaway: Every EO thumbnail should go through at least 3 rounds of iteration before publication.

MrBeast's Visual Clarity Standard:
- The 3-second phone test. Every thumbnail must communicate its message when viewed at phone size for 3 seconds.
- Color saturation and contrast. Use extreme color contrast to stand out in the feed.
- EO takeaway: Test every thumbnail at mobile dimensions before approving.

## **6.4 When to Replace a Thumbnail**

Replace when:
- CTR falls below 4% in the first 48 hours
- A/B test shows a clear winner with statistical significance
- The current thumbnail doesn't reflect the video's strongest moment

## **6.5 Ten Thumbnail Anti-Patterns**

1. No visible gap between two numbers → Rewrite with the formula: small number × big number
2. Text too small at mobile size → 3-5 words max. Test at phone dimensions
3. Neutral facial expression → Use a moment of genuine emotion — surprise, intensity, joy
4. Cluttered background → Simplify or blur. One subject, one message
5. Title repeats thumbnail text exactly → They should complement, not duplicate
6. No clear subject hierarchy → One dominant face. Viewer's eye should have one place to land
7. Framing that damages interviewee's business → Check: could their biggest customer interpret this negatively?
8. Promise the video doesn't deliver → Map thumbnail to intro. The promise must resolve in 30 seconds
9. Generic stock photo aesthetic → Use actual frames from the interview or custom designed graphics
10. No A/B testing before publish → Minimum 3 candidates scored by AI prediction tools

# **PART 7: AI-POWERED 10X PRODUCTION**

EO's position on AI is unambiguous: use it for everything it's good at, and protect the things it can't do. AI handles transcription, research synthesis, rough assembly, thumbnail generation, and data analysis. Humans handle editorial judgment, narrative architecture, emotional calibration, and the final creative decisions that define EO's voice.

## **7.1 The 10x Framework**

AI should make every production phase at least 10x faster than the pre-AI baseline.

Production phases with AI:
- Research & briefing: 8-12 hours → 1-2 hours (~6-8x). LLM research agents, Perplexity.
- Transcription: 2-3 hours → 5 minutes (~30x). Whisper, Assembly AI.
- Storyline / paper edit: 6-10 hours → 1-2 hours (~5x). LLM analysis + human judgment.
- Rough cut assembly: 8-12 hours → 2-3 hours (~4x). AI timeline assembly.
- Thumbnail ideation: 2-3 hours → 30 minutes (~5x). Image gen + prediction scoring.
- Title/copy testing: 1-2 hours → 15 minutes (~6x). LLM brainstorm + scoring.
- B-roll selection: 3-4 hours → 30-45 min (~5x). Visual search + tagging.
- Quality review: 2-3 hours → 30-45 min (~4x). Automated checks + human review.

## **7.2 The EO AI Production Stack**

Pre-Production: Use LLM-powered deep research for subject background, competitive landscape, and market context. Generate the 3 surprises the interviewer needs. Feed previous interviews into an LLM to identify what has never been asked.

Production: Real-time transcript during recording allows the producer to flag key moments immediately. AI flags moments of high emotional intensity, unusual word choice, or statistical claims during the interview.

Post-Production: AI generates a first-pass paper edit from the transcript. AI generates 20-50 thumbnail concepts scored with prediction APIs. AI generates 50+ title options for human filtering.

## **7.3 Five AI Anti-Patterns**

What AI Cannot Do at EO:
1. Choose the editorial angle. AI can generate options. Only a human can decide what EO's perspective is on a subject.
2. Evaluate emotional authenticity. AI can detect vocal intensity. It cannot tell if a moment feels genuine or performed.
3. Protect business relationships. AI doesn't understand that a specific framing could damage an interviewee's relationship with their investors.
4. Replace verification. Every AI-sourced fact must be checked against primary sources. One hallucinated statistic in a published video destroys credibility that took years to build.
5. Substitute for taste. AI can tell you what performed well historically. It cannot tell you what should exist that doesn't yet. EO's editorial instinct is the one thing AI makes more valuable, not less.

# **PART 8: PRODUCTION WORKFLOW**

## **8.1 The AI-Accelerated Production Pipeline**

Phase 1 — Subject research (Day 1): Research briefing with 3 surprises. 80% AI research, 20% human curation.
Phase 2 — Interview prep (Day 1-2): Question sheet + emotional architecture map. AI drafts, human refines angle.
Phase 3 — Interview (Day 2-3): Raw footage + live-flagged highlights. Real-time transcription + flag moments.
Phase 4 — Paper edit (Day 3-4): Editing direction document (not summary). AI generates first pass, human decides structure.
Phase 5 — Rough cut (Day 4-5): Storyline cut — narrative only, no B-roll. AI assembles timeline, human refines.
Phase 6 — Fine cut (Day 5-7): Full edit with B-roll, graphics, music. AI suggests B-roll, human approves.
Phase 7 — Thumbnail/Title (Day 6-7): 3-5 tested candidates for each. AI generates 50+, scores top candidates.
Phase 8 — Quality review (Day 7): Final review against checklist. AI scans technical, human reviews narrative.
Phase 9 — Publish (Day 7-8): Live video with optimized metadata. AI assists SEO, human writes description.

## **8.2 Quality Control Checklist**

Narrative Quality:
- Is there a clear editorial angle that can be stated in one sentence?
- Does the narrative structure match the subject's achievement scale?
- Does each chapter answer exactly one question?
- Does each chapter create curiosity for the next?
- Is the intro delivering on the thumbnail/title promise within 30 seconds?
- Are credentials handled as text overlays, not verbal exposition?
- Are product features shown on screen, never described verbally?

Technical Quality:
- Is editing density maximized — no filler words, no unnecessary repetition?
- Does music support but never compete with the speaker?
- Are all numbers and claims visually reinforced with graphics?
- Are all on-screen facts verified against primary sources?

Strategic Alignment:
- Does the thumbnail follow the copy formula (age/time × achievement gap)?
- Does the title preview what the viewer will learn?
- Is the framing respectful of the interviewee's business interests?
- Has the thumbnail been scored by AI prediction tools?
- Would a US-based startup professional find this worth their time?
- Does this video strengthen EO's position as world-class media?
- Does the target audience have identifiable commercial value? (Remember: viral ≠ monetizable.)
- Would an advertiser or sponsor want to reach the viewers this video attracts?

# **PART 9: LEARNING FROM THE BEST**

## **9.1 Acquired — The Research Depth Standard**

Ben Gilbert and David Rosenthal's Acquired is the most research-intensive podcast in technology media.
- Research hours per episode: 300+ total hours
- Primary source calls: 25-40 per episode
- Script length: 40-70 pages
- Episode structure: Cold open → History (60-75%) → Analysis → Playbook

What EO Takes From Acquired: We can't match 300 hours per episode — our volume doesn't allow it. But we can match the principle: preparation depth is the invisible differentiator. For every marquee EO interview, aim for 5-10 source calls beyond the subject themselves. Also apply E.M. Forster's distinction: "The king died and then the queen died" is a story. "The king died and then the queen died of grief" is a plot. Every section must carry causation, not just chronology.

## **9.2 Diary of a CEO — The Packaging Science Standard**

Steven Bartlett has built the most systematically optimized interview show in the world.
- 1,000-person pre-watch panel. Every episode is tested with 1,000 viewers using eye-tracking before publication.
- 100+ thumbnail concepts per episode. The final thumbnail is chosen by data, not preference.
- Environmental monitoring. CO2 levels in viewing rooms are tracked.
- Question sequencing for novelty. Questions are designed to lead guests into territory they haven't explored publicly.

What EO Takes From DOAC: Bartlett proves that packaging is not a creative afterthought — it's a systematic discipline. Separate "what I like" from "what works." Use data (AI scoring, retention analytics) to override personal preference when they conflict.

## **9.3 Lex Fridman — The Intellectual Respect Standard**

- Years-long preparation. For some guests, Fridman prepares for years before recording.
- The 21-second silence. Fridman sustains silences that would make most interviewers panic.
- Steelmanning as default. Before challenging any position, Fridman articulates the strongest version of the guest's argument.

What EO Takes From Fridman: Respect is a strategy, not just a courtesy. When a guest realizes you've deeply engaged with their work, they stop giving you the rehearsed version and start thinking out loud. That's where EO's best content comes from.

## **9.4 The Synthesis**

Common thread across all world-class interview shows:
1. Preparation depth is the differentiator. Acquired proves it through research hours. Fridman proves it through multi-year relationships. EO proves it through the 'three surprises' standard.
2. Systemize what can be systemized. Bartlett systemizes testing. Acquired systemizes research process. EO should identify which parts of its workflow can become repeatable systems.
3. The anti-pattern is uniformity. Each of these shows has a distinctive voice. EO's strength is the specific combination: Acquired's research rigor + Bartlett's packaging science + Fridman's intellectual respect + EO's own editorial perspective on the startup ecosystem.

# **PART 10: ONBOARDING & COMMON PITFALLS**

## **10.1 New Team Member Path**

1. Read this guide cover to cover. Then read it again.
2. Watch EO's top 10 performing videos. For each one, identify: (a) the narrative type, (b) the thumbnail formula, (c) the strongest moment of intellectual tension, and (d) the emotional arc.
3. Watch EO's 3 lowest-performing videos. For each one, identify: (a) where the narrative breaks, (b) what you'd change about the thumbnail, and (c) where the viewer likely drops off and why.
4. Study the competition. Watch 5 episodes each of 20VC, CNBC Make It, Acquired, and DOAC.
5. Learn the AI toolkit.
6. Produce a practice first edit.
7. Receive feedback and iterate.

## **10.2 Content PD Growth Path**

Level 1 — The Maker: Learn by doing. Volume matters more than quality. Build your body of work — and your stamina.
Level 2 — The Translator: Stop making what you find interesting and start finding the intersection between what you care about and what the audience actually wants. 90% of content producers never reach this level.
Level 3 — The Hit-Maker: You can start small and scale big. You consistently produce above-average performers — not by luck, but by craft.
Level 4 — The Architect: You don't just create content that gets traffic — you build systems that convert that traffic into revenue.
Level 5 — The Pied Piper: You are the person others follow. You can attract talent, build teams, launch new formats, and lead a media network.

Growth Principle: Each level is not a promotion — it is a fundamental shift in how you think. A Lv 1 producer thinks "What should I make?" A Lv 2 producer thinks "What does the audience need?" A Lv 3 producer thinks "How do I make this a hit?" A Lv 4 producer thinks "How does this make money?" A Lv 5 producer thinks "How do I build something bigger than myself?" You cannot skip levels. And the most dangerous place to be is Lv 1 with the confidence of Lv 3.

## **10.3 The 12 Most Common Pitfalls**

1. Using one template for all interviews → Select narrative type based on the interviewee's achievement scale.
2. Defaulting to hero's journey → Ask: "Is this person's journey interesting at every stage?" If not, use situation narrative.
3. Chronological arrangement by default → Chronology is a choice, not a default. Theme-based or tension-based ordering is often stronger.
4. Listing credentials as content → Credentials are text overlays (3 seconds max) or cut entirely.
5. Describing products verbally → Every product feature must be shown on screen with demo footage or B-roll.
6. Producing summaries instead of editing directions → An editing direction says what to cut. A summary says what exists. Different things.
7. Weak thumbnail copy → Apply the formula: Age/Time × Achievement Gap. No gap = no click.
8. Intro doesn't deliver on thumbnail promise → Map intro to thumbnail. The promise must resolve in the first 30 seconds.
9. Ignoring US audience perspective → First question, always: "Would someone in SF or NYC find this interesting?"
10. Conflating effort with quality → Working hard on a bad structure produces a polished bad video. Fix structure first.
11. Using AI outputs without verification → Every AI-sourced fact must be verified. One hallucination destroys years of credibility.
12. Refusing to use AI for appropriate tasks → Not using AI for transcription, research, and rough assembly is wasted time, not craftsmanship.

## **10.4 The Feedback Process**

- Summary vs. direction: First, check: is the document you're reviewing a summary or an editing direction? If it describes what was said but doesn't argue for what to cut, it's a summary. Send it back.
- Right angle, wrong material: Sometimes the topic is perfect but the specific quotes don't support it. This is a selection problem, not a direction problem. Name it precisely.
- The killer quote: In every interview, there is one sentence that could be a title or intro hook. It usually comes when the subject stops performing and starts thinking. Find it before anything else.
- Audience first: Before any other feedback: "Does this work for our audience?" If the answer is no, nothing else matters until that's fixed.
- Efficiency vs. quality distinction: Is this feedback about a genuine quality issue, or a preference that adds cycles without measurably improving the output? Name which one it is.

Every frame is a choice. Every cut is an argument. Every story you tell reflects what you believe matters. Now go make it 10x.
"""

SYSTEM_PROMPT = f"""You are an AI editorial assistant for EO Studio. You have internalized the following Master Storytelling Guide. Every analysis you produce must follow these principles.

{_GUIDE}

Based on the above guide, analyze the given transcript and return a JSON object with:
- narrative_type: object with "type" ("journey" or "situation") and "reasoning" (reference Part 2)
- editorial_perspective: one sentence angle for this video
- chapters: array of objects with "title", "start_quote", "description", "estimated_minutes", "density_score_1_to_10", "intellectual_tension"
- cold_open: object with "quote" and "why_it_works"
- killer_quote: the single best sentence for title/hook (see Part 10.4)
- thumbnail_suggestions: array of strings using the Age/Time x Achievement Gap formula (see Part 6)
- weak_sections: array of objects with "location", "issue", "suggestion"
- pitfall_warnings: array of strings naming which of the 12 common pitfalls (Part 10.3) apply to this content
- audience_test: object with "result" ("yes" or "no") and "reasoning" — would someone in SF/NYC startup ecosystem find this worth 15 minutes?
- overall_assessment: one paragraph on how to package this

Return ONLY valid JSON — no markdown fences, no extra commentary."""


class AnalyzeRequest(BaseModel):
    transcript: str
    video_topic: str | None = None
    target_audience: str | None = None
    video_length_target: int | None = 20
    series: str | None = None
    use_rag: bool = True


def _build_prompt(body: AnalyzeRequest, similar_cases: list[dict] | None = None) -> str:
    # Build a natural-language context sentence from optional fields
    parts = []
    if body.series:
        parts.append(f"This is a {body.series} episode")
    if body.target_audience:
        parts.append(f"targeting {body.target_audience}")
    if body.video_length_target:
        parts.append(f"aiming for {body.video_length_target} minutes")
    if body.video_topic:
        parts.append(f"on the topic: {body.video_topic}")

    lines = []
    if parts:
        lines.append(", ".join(parts) + ".")
        lines.append("")

    if similar_cases:
        lines.append("## Similar Past EO Projects (for reference)")
        lines.append(
            "The following excerpts are from real EO transcripts that are semantically "
            "similar to this one. Reference them when reasoning about narrative type, "
            "chapter structure, and packaging — but do not copy them directly."
        )
        lines.append("")
        for i, case in enumerate(similar_cases, 1):
            lines.append(
                f"### Case {i}: {case['title']} "
                f"(similarity: {case['similarity_score']}, project_id: {case['project_id']})"
            )
            lines.append(case["matching_chunk"][:600])
            lines.append("")
        lines.append("---")
        lines.append("")

    lines.append(f"Transcript:\n\n{body.transcript}")
    return "\n".join(lines)


def get_client() -> anthropic.Anthropic:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="ANTHROPIC_API_KEY is not set. Add it to your .env file.",
        )
    return anthropic.Anthropic(api_key=api_key)


@app.post("/analyze")
def analyze(body: AnalyzeRequest):
    if not body.transcript.strip():
        raise HTTPException(status_code=400, detail="transcript must not be empty")

    similar_cases = None
    if body.use_rag:
        try:
            similar_cases = search_similar(body.transcript[:2000], n_results=3)
        except Exception:
            similar_cases = None  # RAG failure should not block analysis

    client = get_client()

    try:
        with client.messages.stream(
            model=MODEL,
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": _build_prompt(body, similar_cases)}],
        ) as stream:
            message = stream.get_final_message()
    except anthropic.AuthenticationError:
        raise HTTPException(status_code=500, detail="Invalid Anthropic API key.")
    except anthropic.RateLimitError:
        raise HTTPException(status_code=429, detail="Anthropic rate limit reached. Try again later.")
    except anthropic.APIStatusError as exc:
        raise HTTPException(status_code=502, detail=f"Anthropic API error {exc.status_code}: {exc.message}")
    except anthropic.APIConnectionError:
        raise HTTPException(status_code=502, detail="Could not connect to Anthropic API. Check your network.")

    raw = message.content[0].text.strip()

    # Strip markdown code fences if present
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[-1]
    if raw.endswith("```"):
        raw = raw.rsplit("```", 1)[0].strip()

    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        result = {"error": True, "raw": raw}

    result["similar_cases_used"] = similar_cases or []
    return result


# ---------------------------------------------------------------------------
# RAG endpoints
# ---------------------------------------------------------------------------

class SearchRequest(BaseModel):
    transcript: str
    n_results: int = 3


@app.post("/seed")
def seed():
    try:
        stats = seed_from_dataset()
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return stats


@app.post("/search")
def search(body: SearchRequest):
    if not body.transcript.strip():
        raise HTTPException(status_code=400, detail="transcript must not be empty")
    results = search_similar(body.transcript, n_results=body.n_results)
    return {"results": results}


@app.get("/projects")
def list_projects():
    try:
        data = json.loads(__import__("pathlib").Path("data/dataset.json").read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="dataset.json not found. Run build_dataset.py first.")
    return {
        "projects": [
            {
                "project_id": p["project_id"],
                "title": p["title"],
                "character_count": p["character_count"],
            }
            for p in data.get("projects", [])
        ]
    }


@app.get("/projects/{project_id}")
def project_detail(project_id: str):
    proj = get_project(project_id)
    if proj is None:
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found.")
    return proj


# ---------------------------------------------------------------------------
# Analyze V2 — full story analysis pipeline
# ---------------------------------------------------------------------------

ANALYZE_V2_SYSTEM = f"""You are an AI editorial assistant for EO Studio. You have internalized the following Master Storytelling Guide. Every analysis you produce must follow these principles.

{_GUIDE}

You will receive:
1. A full interview transcript
2. Story chunks with their topics and emotional tones
3. For each chunk: similar past EO projects, their performance data (views, retention ratio), and whether similar content survived into the final edited video

Based on ALL of this, return a JSON object with the structure below.

IMPORTANT RULES:
- Your KEEP/CUT/SHORTEN recommendations MUST reference actual past performance data provided.
- Chapter options should mirror structures from high-performing past videos.
- Warnings must be specific (cite chunk numbers and past video data).
- Opportunities should identify rare or strong content relative to the EO library.

Return ONLY valid JSON — no markdown fences, no extra commentary.

JSON structure:
{{
  "narrative_type": {{"type": "journey|situation", "reasoning": "..."}},
  "editorial_perspective": "one sentence angle",
  "story_chunks": [
    {{
      "chunk_id": 1,
      "topic": "...",
      "estimated_minutes": 2.5,
      "recommendation": "KEEP|CUT|SHORTEN",
      "confidence": "high|medium|low",
      "reasoning": "...",
      "similar_past": [
        {{"project": "...", "similarity": 0.72, "retention": 0.55, "survived": true, "views": 1549651}}
      ],
      "editing_note": "..."
    }}
  ],
  "chapter_options": [
    {{
      "option": "A",
      "structure": [
        {{"chapter": 1, "title": "...", "chunks_included": [3, 4], "estimated_minutes": 4}}
      ],
      "reasoning": "..."
    }}
  ],
  "target_compression": 0.25,
  "estimated_final_length_minutes": 12,
  "warnings": ["..."],
  "opportunities": ["..."],
  "killer_quote": "...",
  "cold_open": {{"quote": "...", "why_it_works": "..."}},
  "thumbnail_suggestions": ["..."]
}}"""


class AnalyzeV2Request(BaseModel):
    transcript: str
    video_length_target: int = 15
    weight_retention: float = 0.4


@app.post("/analyze-v2")
def analyze_v2(body: AnalyzeV2Request):
    if not body.transcript.strip():
        raise HTTPException(status_code=400, detail="transcript must not be empty")

    # STEP A: Story-chunk the transcript
    try:
        chunks = chunk_transcript(body.transcript)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Chunking failed: {exc}")

    # STEP B: For each chunk, find similar past content
    chunk_search_results = []
    for chunk in chunks:
        chunk_text = chunk.get("text", "")
        if not chunk_text.strip():
            chunk_search_results.append([])
            continue
        try:
            similar = search_similar(
                chunk_text[:2000],
                n_results=3,
                weight_retention=body.weight_retention,
            )
        except Exception:
            similar = []
        chunk_search_results.append(similar)

    # STEP C: Build context for Claude
    context_lines = []
    context_lines.append(f"Target video length: {body.video_length_target} minutes")
    context_lines.append(f"Total transcript chunks: {len(chunks)}")
    total_est = sum(c.get("estimated_minutes", 0) for c in chunks)
    context_lines.append(f"Total estimated raw minutes: {total_est:.1f}")
    context_lines.append("")

    for i, (chunk, similar) in enumerate(zip(chunks, chunk_search_results)):
        context_lines.append(
            f"### Chunk {chunk['chunk_id']}: {chunk['topic']} "
            f"({chunk['estimated_minutes']:.1f} min, {chunk['emotional_tone']})"
        )
        context_lines.append(f"Summary: {chunk['summary']}")
        if similar:
            context_lines.append("Similar past projects:")
            for s in similar:
                surv = "KEPT in edit" if s["survived_editing"] else "CUT from edit"
                context_lines.append(
                    f"  - {s['title']} (sim={s['similarity_score']:.2f}, "
                    f"retention={s.get('retention_ratio', 'N/A')}, "
                    f"views={s['views']:,}, {surv})"
                )
        context_lines.append("")

    context_lines.append("---")
    context_lines.append("")
    # Include first 30000 chars of transcript to stay within limits
    context_lines.append(f"Full Transcript (first 30000 chars):\n\n{body.transcript[:30000]}")

    user_content = "\n".join(context_lines)

    # STEP D: Call Claude
    client = get_client()
    try:
        message = client.messages.create(
            model=MODEL,
            max_tokens=8192,
            system=ANALYZE_V2_SYSTEM,
            messages=[{"role": "user", "content": user_content}],
        )
    except anthropic.AuthenticationError:
        raise HTTPException(status_code=500, detail="Invalid Anthropic API key.")
    except anthropic.RateLimitError:
        raise HTTPException(
            status_code=429, detail="Anthropic rate limit reached. Try again later."
        )
    except anthropic.APIStatusError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Anthropic API error {exc.status_code}: {exc.message}",
        )
    except anthropic.APIConnectionError:
        raise HTTPException(
            status_code=502,
            detail="Could not connect to Anthropic API. Check your network.",
        )

    raw = message.content[0].text.strip()

    if raw.startswith("```"):
        raw = raw.split("\n", 1)[-1]
    if raw.endswith("```"):
        raw = raw.rsplit("```", 1)[0].strip()

    # Parse JSON robustly: Haiku often appends markdown commentary after valid JSON.
    # Strategy: try raw first, strip trailing ```, then brace-match as last resort.
    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        # Haiku pattern: valid JSON followed by ``` then markdown commentary
        if "```" in raw:
            stripped = raw[: raw.index("```")].strip()
            try:
                result = json.loads(stripped)
            except (json.JSONDecodeError, ValueError):
                result = None
        else:
            result = None
        if result is None:
            # Last resort: find the first complete JSON object by brace-matching
            start = raw.find("{")
            if start != -1:
                depth = 0
                in_string = False
                escape_next = False
                for i in range(start, len(raw)):
                    ch = raw[i]
                    if escape_next:
                        escape_next = False
                        continue
                    if ch == "\\":
                        if in_string:
                            escape_next = True
                        continue
                    if ch == '"' and not escape_next:
                        in_string = not in_string
                        continue
                    if in_string:
                        continue
                    if ch == "{":
                        depth += 1
                    elif ch == "}":
                        depth -= 1
                        if depth == 0:
                            try:
                                result = json.loads(raw[start : i + 1])
                            except json.JSONDecodeError:
                                pass
                            break
            if result is None:
                result = {"error": True, "raw": raw}

    # STEP E: Attach raw data for transparency
    result["_raw_chunks"] = chunks
    result["_chunk_search_results"] = [
        [
            {
                "project_id": s["project_id"],
                "title": s["title"],
                "similarity_score": s["similarity_score"],
                "retention_ratio": s.get("retention_ratio"),
                "combined_score": s["combined_score"],
                "views": s["views"],
                "survived_editing": s["survived_editing"],
            }
            for s in similar
        ]
        for similar in chunk_search_results
    ]

    return result


# ---------------------------------------------------------------------------
# Script comparison endpoint
# ---------------------------------------------------------------------------

@app.post("/compare/{project_id}")
def compare_project(project_id: str):
    proj = get_project(project_id)
    if proj is None:
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found.")

    original = proj.get("transcript_original", "")
    edited = proj.get("transcript_edited", "")

    if not original or not edited:
        raise HTTPException(
            status_code=400,
            detail="Project must have both transcript_original and transcript_edited.",
        )

    # Chunk both transcripts
    orig_chunks = chunk_transcript(original, project_id=f"{project_id}__original")
    edit_chunks = chunk_transcript(edited, project_id=f"{project_id}__edited")

    # Check survival of each original chunk
    from rapidfuzz import fuzz

    chunk_analysis = []
    topics_kept = []
    topics_cut = []
    compression_ratios = []

    for oc in orig_chunks:
        oc_text = oc.get("text", "")
        if not oc_text.strip():
            continue

        # Find best matching edited chunk
        best_score = 0
        best_edit_chunk = None
        for ec in edit_chunks:
            ec_text = ec.get("text", "")
            if not ec_text.strip():
                continue
            score = fuzz.partial_ratio(oc_text[:300], ec_text)
            if score > best_score:
                best_score = score
                best_edit_chunk = ec

        survived = best_score >= 55
        entry = {
            "original_chunk_id": oc["chunk_id"],
            "topic": oc["topic"],
            "summary": oc["summary"],
            "original_minutes": oc["estimated_minutes"],
            "survived": survived,
        }

        if survived and best_edit_chunk:
            entry["edited_minutes"] = best_edit_chunk["estimated_minutes"]
            if oc["estimated_minutes"] > 0:
                comp = round(
                    best_edit_chunk["estimated_minutes"] / oc["estimated_minutes"], 2
                )
                entry["compression"] = comp
                compression_ratios.append(comp)
            entry["note"] = (
                f"Shortened — kept core content from '{oc['topic']}'"
                if best_edit_chunk["estimated_minutes"] < oc["estimated_minutes"]
                else f"Kept at similar length"
            )
            topics_kept.append(oc["topic"])
        else:
            entry["note"] = "Completely cut from final video"
            topics_cut.append(oc["topic"])

        chunk_analysis.append(entry)

    # Performance data
    perf = proj.get("performance", {})

    # Compile patterns
    avg_compression = (
        round(sum(compression_ratios) / len(compression_ratios), 2)
        if compression_ratios
        else None
    )

    # Deduplicate topic lists
    kept_unique = list(dict.fromkeys(topics_kept))
    cut_unique = list(dict.fromkeys(topics_cut))

    # Generate insight
    insight_parts = []
    if cut_unique:
        insight_parts.append(f"Cut topics: {', '.join(cut_unique)}.")
    if kept_unique:
        insight_parts.append(f"Kept topics: {', '.join(kept_unique)}.")
    retention = proj.get("retention_ratio")
    if retention:
        insight_parts.append(f"Result: {retention:.0%} retention ratio.")

    return {
        "project_id": project_id,
        "title": proj.get("title", ""),
        "compression_ratio": proj.get("compression_ratio"),
        "original_chunks": len(orig_chunks),
        "edited_chunks": len(edit_chunks),
        "performance": {
            "views": perf.get("views", 0),
            "likes": perf.get("likes", 0),
            "retention_ratio": retention,
        },
        "chunk_analysis": chunk_analysis,
        "patterns": {
            "topics_kept": kept_unique,
            "topics_cut": cut_unique,
            "avg_compression_for_kept": avg_compression,
            "insight": " ".join(insight_parts),
        },
    }
