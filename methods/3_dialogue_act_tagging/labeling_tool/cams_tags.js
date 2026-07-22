/* CAMS dialogue-act tag metadata - single source of truth for BOTH codebook.html and ui.html.
   Definitions/examples condensed from implementation/CAMS_LLM_labeling_prompt.txt (the exact
   text the LLM tagger was given). Categories are CAMS's own eight function groups, in the
   schema's own order. 27 tags + `none` = 28, matching signals.py TAGS. */

window.CAMS_CATEGORIES = [
  {
    id: "seeking",
    name: "Information-seeking",
    blurb: "You want something FROM the other side. All of these put pressure on someone to respond.",
    color: "seek",
    tags: [
      { tag: "propositionalQuestion", short: "Yes/No question",
        def: "Asks whether a proposition is true. Speaker does NOT already lean either way.",
        ex: ["Does the meeting start at ten?", "Is everyone available?"] },
      { tag: "setQuestion", short: "Wh- question",
        def: "Asks which element(s) of an open set have some property. Who/what/where/when/how.",
        ex: ["What time does the meeting start?", "How far is it to the station?"] },
      { tag: "choiceQuestion", short: "Pick one from a list",
        def: "Asks which ONE of an explicitly given list of alternatives is true.",
        ex: ["Should the cable go in telephone line or external line?"] },
      { tag: "checkQuestion", short: "Confirm-my-hunch question",
        def: "Yes/No question where the speaker ALREADY holds an uncertain belief and wants it verified.",
        ex: ["The meeting starts at ten, right?", "So that's 12, isn't it?"] }
    ]
  },
  {
    id: "providing",
    name: "Information-providing",
    blurb: "You are giving information. The biggest and most-used group - `inform` alone is ~61% of the monologue cells.",
    color: "prov",
    tags: [
      { tag: "inform", short: "Statement (unsolicited)",
        def: "Makes information known. Speaker assumes it is correct. Covers explaining, elaborating, exemplifying, justifying. NOT a response to a question.",
        ex: ["The 6.34 to Breda leaves from platform 2.", "But this does not give us 24."] },
      { tag: "answer", short: "Statement (solicited)",
        def: "Provides information the speaker believes the addressee WANTS to know - i.e. responds to a prior question.",
        ex: ["Q: What does the display say?  ->  A: Send error document ready."] },
      { tag: "agreement", short: "I also think that's true",
        def: "Informs that speaker assumes a proposition to be true, which they believe the addressee also assumes true.",
        ex: ["Exactly.", "Yeah, I think so too."] },
      { tag: "disagreement", short: "I think that's false",
        def: "Informs that speaker assumes a proposition to be false, which the addressee assumes true.",
        ex: ["Uh... no.", "I don't think that works."] },
      { tag: "correction", short: "That's wrong, here's the right one",
        def: "Tells addressee that information they believe correct is in fact incorrect, AND supplies the correct version.",
        ex: ["To Montreal, not to Ottawa."] },
      { tag: "confirm", short: "Yes, your hunch is right",
        def: "Confirms information the addressee wanted to know and held an UNCERTAIN belief about. The natural reply to a checkQuestion.",
        ex: ["Indeed.", "Yes, that's correct."] },
      { tag: "disconfirm", short: "No, your hunch is wrong",
        def: "Tells addressee that the thing they held an uncertain belief about is incorrect.",
        ex: ["Nope.", "No, it's not."] }
    ]
  },
  {
    id: "commissive",
    name: "Commissive",
    blurb: "About what the SPEAKER will or won't do. Commits (or refuses to commit) the speaker to an action.",
    color: "comm",
    tags: [
      { tag: "offer", short: "I'll do it, if you want",
        def: "Speaker indicates willingness and ability to perform an action, conditional on addressee's consent.",
        ex: ["I will look that up for you."] },
      { tag: "conditionalAccept", short: "Yes, but only if...",
        def: "Speaker will consider/commit to the action, but makes an explicit condition.",
        ex: ["A: Please give me the gun.  ->  S: If you push the bag to me."] },
      { tag: "accept", short: "Yes, I'll do it",
        def: "Speaker commits to performing a requested/suggested action, or accepts an offer.",
        ex: ["A: Would you like help with that?  ->  S: Sure."] },
      { tag: "decline", short: "No, I won't",
        def: "Speaker refuses to perform a requested/suggested action, or turns down an offer.",
        ex: ["A: Would you like help with that?  ->  S: No thank you."] }
    ]
  },
  {
    id: "directive",
    name: "Directive",
    blurb: "About what the OTHER PERSON should do. Mirror image of Commissive.",
    color: "dir",
    tags: [
      { tag: "request", short: "Please do this (for me)",
        def: "Creates a commitment for the addressee to perform an action, conditional on their consent.",
        ex: ["Please turn to page five.", "Please drive very carefully."] },
      { tag: "suggest", short: "Maybe we/you should...",
        def: "Makes the addressee consider performing an action that the speaker believes is in the ADDRESSEE'S interest.",
        ex: ["Let's wait for the speaker to finish.", "You could try multiplying first."] }
    ]
  },
  {
    id: "feedback",
    name: "Feedback",
    blurb: "Signals whether the speaker successfully PROCESSED what was just said. Not about agreeing - about understanding.",
    color: "fb",
    tags: [
      { tag: "autoPositive", short: "Got it / uh-huh",
        def: "Signals that the speaker's processing of the previous utterance(s) was successful.",
        ex: ["Uh-huh", "Okay", "Yes", "I see"] },
      { tag: "autoNegative", short: "Huh? / didn't catch that",
        def: "Signals that the speaker's processing of the previous utterance(s) hit a problem.",
        ex: ["Sorry?", "What?"] }
    ]
  },
  {
    id: "time",
    name: "Time Management",
    blurb: "Buying time. No content of its own.",
    color: "time",
    tags: [
      { tag: "stalling", short: "Um... let me think",
        def: "Buys the speaker a little extra time to construct their contribution, or briefly suspends the dialogue.",
        ex: ["Let me see...", "Ehm...", "Just a moment", "Umm..."] }
    ]
  },
  {
    id: "ocm",
    name: "Own/Partner Communication Management",
    blurb: "Repairing the speaker's own utterance mid-flight.",
    color: "ocm",
    tags: [
      { tag: "retraction", short: "Scratch that",
        def: "Withdraws or abandons something the speaker just said WITHIN THE SAME TURN.",
        ex: ["Then we're going to g-", "Wait, no."] }
    ]
  },
  {
    id: "social",
    name: "Social Obligations Management",
    blurb: "Ritual politeness moves. Nearly always come in pairs. Rare in reasoning/debate data.",
    color: "soc",
    tags: [
      { tag: "greeting", short: "Hello",
        def: "Informs the addressee that the speaker is present and aware of their presence.",
        ex: ["Hello!", "Good morning"] },
      { tag: "goodbye", short: "Bye",
        def: "Signals the speaker intends this to be their final contribution.",
        ex: ["Bye bye, see you later."] },
      { tag: "thanking", short: "Thanks",
        def: "Expresses gratitude for some action performed by the addressee.",
        ex: ["Thanks a lot."] },
      { tag: "acceptThanking", short: "You're welcome",
        def: "Mitigates the gratitude the addressee expressed.",
        ex: ["Don't mention it.", "No problem."] },
      { tag: "apology", short: "Sorry",
        def: "Signals the speaker regrets something; puts pressure on addressee to acknowledge.",
        ex: ["Sorry about that."] },
      { tag: "acceptApology", short: "It's fine",
        def: "Mitigates the regret the addressee expressed.",
        ex: ["No problem.", "That's alright."] }
    ]
  },
  {
    id: "fallback",
    name: "Fallback",
    blurb: "Last resort only.",
    color: "none",
    tags: [
      { tag: "none", short: "No speech act at all",
        def: "Use ONLY if the sentence clearly matches none of the 27 tags AND does not form a speech act. The tagger was told to try the 27 first - you should too.",
        ex: ["(fragment, garbled text, pure formatting noise)"] }
    ]
  }
];

/* The confusions most likely to cost you kappa. Each is a pair/cluster that shares surface form
   but differs in communicative function - which is what CAMS actually keys on. */
window.CAMS_CONFUSIONS = [
  {
    title: "propositionalQuestion vs. checkQuestion",
    ask: "Does the speaker already have a hunch?",
    rows: [
      ["propositionalQuestion", "Genuinely open Yes/No. No prior lean.", "Is it 24?"],
      ["checkQuestion", "Speaker already believes it, wants verification. Often has a tag: right? isn't it? so...?", "It's 24, right?"]
    ]
  },
  {
    title: "setQuestion vs. choiceQuestion",
    ask: "Was an explicit list of alternatives given in the sentence?",
    rows: [
      ["setQuestion", "Open set. Wh-word. Any number of answers possible.", "Which numbers should we use?"],
      ["choiceQuestion", "Closed, explicitly stated list. Exactly one is true.", "Should we use 6 or 8?"]
    ]
  },
  {
    title: "inform vs. answer",
    ask: "Is there a question immediately before it that this responds to?",
    rows: [
      ["inform", "Unsolicited. Speaker volunteers it.", "The total is 24."],
      ["answer", "Solicited. Responds to a prior question.", "Q: What's the total? -> 24."]
    ]
  },
  {
    title: "agreement vs. confirm vs. autoPositive vs. accept",
    ask: "All four can surface as 'yes'. What is the yes ABOUT?",
    rows: [
      ["agreement", "About a PROPOSITION we both hold true.", "Yes, that's a good approach."],
      ["confirm", "About the addressee's UNCERTAIN BELIEF (answers a checkQuestion).", "Q: It's 24, right? -> Yes."],
      ["autoPositive", "About UNDERSTANDING - I processed what you said.", "Okay. / Uh-huh."],
      ["accept", "About an ACTION - I commit to doing it.", "Q: Can you check? -> Sure."]
    ]
  },
  {
    title: "disagreement vs. disconfirm vs. correction vs. decline",
    ask: "The mirror image of the above. What is the no ABOUT?",
    rows: [
      ["disagreement", "About a proposition - I think it's false.", "No, that doesn't follow."],
      ["disconfirm", "About the addressee's uncertain belief.", "Q: It's 24, right? -> No."],
      ["correction", "About wrong info + supplies the right value.", "Not 24, it's 26."],
      ["decline", "About an action - I refuse to do it.", "Q: Can you check? -> No."]
    ]
  },
  {
    title: "request vs. suggest vs. offer",
    ask: "Who performs the action, and in whose interest?",
    rows: [
      ["request", "ADDRESSEE acts, at speaker's behest.", "Please add those up."],
      ["suggest", "ADDRESSEE (or both) acts, in addressee's interest.", "You could try adding those."],
      ["offer", "SPEAKER acts, pending addressee's consent.", "I'll add those up for you."]
    ]
  },
  {
    title: "stalling vs. retraction vs. none",
    ask: "Content-free utterances - which kind of empty?",
    rows: [
      ["stalling", "Buying time, nothing withdrawn.", "Hmm, let me think..."],
      ["retraction", "Abandoning something just said, same turn.", "So we take 6- no wait."],
      ["none", "Not a speech act at all. Genuine last resort.", "(garbled fragment)"]
    ]
  }
];

/* Practical notes specific to THIS dataset, not part of CAMS itself. */
window.CAMS_DATASET_NOTES = [
  "Two of the four cells (human_monologue, ai_monologue) are a single person reasoning alone. Most sentences there are plain <b>inform</b> - that is expected, not a sign you are doing it wrong. The observed marginals have inform at roughly 61% in cell 1.",
  "In monologue data, a person can still ask themselves questions (<b>setQuestion</b>, <b>propositionalQuestion</b>) and answer them. Rhetorical self-questions are still questions - tag by the communicative function of the sentence, not by whether a second speaker exists.",
  "Social tags (greeting/goodbye/thanking/apology and their accept- partners) are genuinely rare in this data. If you find yourself reaching for them often, re-read the sentence.",
  "The tagger was instructed: if a sentence continues the SAME speech act as the previous sentence, keep the same tag. You are labeling sentences in isolation here (deliberately - it keeps the comparison blind), so judge each on its own communicative function.",
  "You will not always be sure. Pick the best single fit and move on - kappa is computed over 510 items and tolerates individual coin-flips far better than it tolerates you stopping to agonize."
];
