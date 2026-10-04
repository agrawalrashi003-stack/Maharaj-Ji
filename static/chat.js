// =====================================================
// MAHARAJ JI — FOOD AGENT
// SAME BRAIN FOR VOICE + TEXT
// =====================================================

let socket = null;
let audioContext = null;
let microphoneStream = null;
let microphoneSource = null;
let processor = null;

let wakeRecognition = null;
let wakeRecognitionRunning = false;

let maharajActive = false;
let waitingForWakeWord = true;
let endingConversation = false;
let voiceMode = false;
let setupComplete = false;

let pendingTextMessages = [];

let audioQueue = [];
let isPlaying = false;
let currentAudioSource = null;
let nextAudioTime = 0;

let currentUserBubble = null;
let currentAssistantBubble = null;

let lastRecommendedMealText = "";


// =====================================================
// DOM
// =====================================================

const orb = document.getElementById("voice-orb");
const statusText = document.getElementById("voice-status");
const chatContainer = document.getElementById("chat-container");
const messageInput = document.getElementById("message-input");
const sendButton = document.getElementById("send-button");


// =====================================================
// UI
// =====================================================

function setState(state, message) {
    if (orb) {
        orb.classList.remove(
            "listening",
            "thinking",
            "speaking"
        );

        if (state) orb.classList.add(state);
    }

    if (statusText) {
        statusText.textContent = message;
    }
}

function addMessage(text, type) {
    if (!chatContainer) return null;

    const message = document.createElement("div");

    message.className =
        "message " +
        (type === "user"
            ? "user-message"
            : "assistant-message");

    message.textContent = text;

    chatContainer.appendChild(message);
    chatContainer.scrollTop = chatContainer.scrollHeight;

    return message;
}

function appendBubbleText(bubble, text) {
    if (!bubble || !text) return;

    bubble.textContent += text;

    chatContainer.scrollTop =
        chatContainer.scrollHeight;
}


// =====================================================
// CREATE GEMINI LIVE SESSION
// =====================================================

async function createLiveSession() {

    if (socket || setupComplete) return;

    endingConversation = false;

    setState(
        "thinking",
        "Starting Maharaj Ji..."
    );

    try {

        const tokenResponse =
            await fetch("/api/live-token", {
                method: "POST"
            });

        const tokenData =
            await tokenResponse.json();

        if (
            !tokenResponse.ok ||
            !tokenData.token
        ) {
            throw new Error(
                tokenData.error ||
                "Could not create Live token."
            );
        }

        const websocketUrl =
            "wss://generativelanguage.googleapis.com/ws/" +
            "google.ai.generativelanguage.v1beta." +
            "GenerativeService.BidiGenerateContentConstrained" +
            "?access_token=" +
            encodeURIComponent(tokenData.token);

        socket =
            new WebSocket(websocketUrl);

        socket.onopen = () => {

            console.log(
                "MAHARAJ JI LIVE CONNECTED"
            );

            socket.send(
                JSON.stringify({

                    setup: {

                        model:
                            "models/gemini-3.8-live",

                        generationConfig: {

                            responseModalities: [
                                "AUDIO"
                            ],

                            speechConfig: {
                                voiceConfig: {
                                    prebuiltVoiceConfig: {
                                        voiceName: "Puck"
                                    }
                                }
                            }
                        },

                        tools: [
                            {
                                functionDeclarations: [
                                    {
                                        name:
                                            "run_food_agent",

                                        description:
    "Run Maharaj Ji's food backend when enough information is available to make or update a concrete food decision. MUST also be called when the user explicitly confirms the currently recommended meal, for example: 'Okay, I will cook this', 'Okay, I'll cook it', 'Yes, I'll make this', 'Yes, let's make it', 'I'll go with this', or 'Let's cook this'. The backend must receive the confirmation so it can record the confirmed meal in cooking history.",
                                        parameters: {
                                            type: "OBJECT",

                                            properties: {
                                              user_message: {
    type: "STRING",
    description:
        "The latest user request including relevant food constraints."
},

recommended_meal: {
    type: "OBJECT",
    description:
        "The exact meal Maharaj Ji has currently recommended to the user. Include this whenever a concrete meal has been recommended or selected.",
    properties: {
        name: {
            type: "STRING"
        },
        reason: {
            type: "STRING"
        },
        description: {
            type: "STRING"
        },
        ingredients: {
            type: "ARRAY",
            items: {
                type: "STRING"
            }
        },
        preparation_time: {
            type: "NUMBER"
        },
        estimated_cost: {
            type: "NUMBER"
        }
    }
}
                                            },

                                            required: [
                                                "user_message"
                                            ]
                                        }
                                    }
                                ]
                            }
                        ],

                        

                        inputAudioTranscription: {},
                        outputAudioTranscription: {},

                        sessionResumption: {},

                        systemInstruction: {
                            parts: [
                                {
                                    text: `
You are Maharaj Ji, a personal food agent.

YOUR ONLY PURPOSE:
Help the user get their meal sorted today.

You are NOT a general-purpose AI assistant.
You are NOT ChatGPT.
Stay strictly within your food-agent role.

PERSONALITY:
Warm, calm, practical, conversational, concise and helpful.
Speak naturally.
Do not sound robotic.
Do not behave like a questionnaire.
Do not over-explain.

LANGUAGE:
Use English by default.
If the user speaks Hindi or Hinglish, respond naturally in Hindi/Hinglish.
Do not randomly switch languages.

FOOD SCOPE:
You can help with:
- deciding what to eat
- deciding what to cook
- meal planning
- recipes
- cooking
- ingredients
- groceries
- cravings
- cuisines
- dietary preferences
- allergies
- cooking time
- budget
- number of people
- available ingredients
- missing ingredients
- grocery sourcing
- food ordering
- cooking assistance
- meal feedback
- food preferences

Personal context such as tiredness, busyness, celebrations, guests or mood may be used ONLY when it helps make a food decision.

OUT OF SCOPE:
Do NOT answer:
- general knowledge
- coding
- programming
- mathematics
- academics
- technology
- news
- politics
- finance
- entertainment
- travel
- sports
- history
- unrelated science
- relationship advice
- medical advice
- legal advice
- unrelated topics

For an unrelated request:
DO NOT answer it.
DO NOT call run_food_agent.

Give a short redirect such as:
"I'm your food agent, so I can't help with that. But I can help you decide what to eat today."

CONVERSATION:
This is ONE continuous conversation.
Remember information already provided during the current Live session.
If the user changes a requirement, update the existing plan.
Do not restart unnecessarily.
Do not ask for information already provided.
Do not ask everything at once.
Ask only what is genuinely needed.

A pause does NOT end the conversation.
turnComplete does NOT end the conversation.

UNDERSTANDING:
Depending on the situation, you may need:
- dietary preference
- allergies
- craving
- available ingredients
- cooking time
- budget
- number of people
- willingness to cook

Ask only for genuinely missing information.

FOOD TOOL:

You have access to:

run_food_agent

CRITICAL RULE:

Whenever you are about to recommend a concrete meal, you MUST call run_food_agent FIRST.

NEVER give a concrete meal recommendation directly without calling run_food_agent.

When calling run_food_agent and you have already chosen a specific meal, ALWAYS include that exact meal in recommended_meal.

If the user explicitly confirms the currently recommended meal, such as:

"Okay, I'll cook this"
"I'll make this"
"Yes, I'll make this"
"Let's cook this"
"I'll go with this"
"This sounds good"

you MUST call run_food_agent again.

For confirmation calls, ALWAYS include the exact currently recommended meal in recommended_meal.

The backend must receive the exact meal so it can record that meal in cooking history.

Do NOT skip the tool call just because you already know the answer.

Use run_food_agent ONLY for food-related requests.

Use it when enough information is available to make or update a concrete food decision.

Examples:
"What should I cook?"
"What should I eat tonight?"
"I want something spicy."
"I have paneer."
"I don't want paneer anymore."
"What can I make with what I have?"
"I need groceries for this meal."

Do NOT call it for unrelated questions.

The backend is the source of truth for:
- meal decisions
- inventory
- missing ingredients
- sourcing

If important food information is genuinely missing, ask a natural clarification first.

Never invent backend results.

REJECTION / REPLANNING:
If the user rejects a meal:
DO NOT restart.
Understand why.
Update the relevant constraint.
Replan.

If the user changes their mind:
Update the current plan.
Do not restart.

If requirements conflict:
Do not silently choose one.
Briefly explain the conflict and ask which requirement to relax.

STOP:
If the user clearly wants to end the interaction, STOP immediately.

Recognize phrases including:
stop
okay stop
ok stop
stop now
stop talking
stop speaking
please stop
keep quiet
please keep quiet
be quiet
please be quiet
that's enough
that's all
that's it
we're done
goodbye
bye
continue later
I don't need anything else

Hinglish:
bas
bas karo
bas kar do
band karo
ab bas
ab bas karo
chup
chup raho
chup karo
chup ho jao
chup reh
shant raho
shaant raho
shant ho jao
shaant ho jao
itna hi
mujhe aur kuch nahi chahiye

Hindi:
चुप
चुप रहो
चुप करो
चुप हो जाओ
शांत रहो
शांत हो जाओ
बस
बस करो
अब बस
बंद करो
बोलना बंद करो
इतना ही
मुझे और कुछ नहीं चाहिए

When the user clearly asks you to stop:
DO NOT call run_food_agent.
DO NOT ask another question.
DO NOT continue the food conversation.
The browser will terminate the active conversation.

AFTER NORMAL ANSWERS:
Remain ready for the next message.
Do not say goodbye automatically.
Only an explicit ending command ends the interaction.

RESPONSE STYLE:
Keep responses concise and natural.
Do not behave like a generic AI assistant.

Your job:
HELP THE USER GET THEIR MEAL SORTED TODAY.
`
                                }
                            ]
                        }
                    }
                })
            );

            console.log(
                "MAHARAJ JI SETUP SENT"
            );
        };

        socket.onmessage =
            handleLiveMessage;

        socket.onerror =
            (error) => {

                console.error(
                    "GEMINI LIVE ERROR:",
                    error
                );

                if (!endingConversation) {
                    setState(
                        "",
                        "Maharaj Ji voice connection error."
                    );
                }
            };

        socket.onclose =
            (event) => {

                console.log(
                    "MAHARAJ JI CONNECTION CLOSED:",
                    event.code,
                    event.reason
                );

                stopMicrophone();
                stopAudio();

                socket = null;
                setupComplete = false;

                if (!endingConversation) {

                    maharajActive = false;
                    waitingForWakeWord = true;
                    voiceMode = false;

                    setState(
                        "",
                        'Say "Hi Maharaj Ji" to wake me.'
                    );

                    startWakeWordListener();
                }
            };

    } catch (error) {

        console.error(
            "START MAHARAJ JI ERROR:",
            error
        );

        socket = null;
        setupComplete = false;
        maharajActive = false;
        waitingForWakeWord = true;

        setState(
            "",
            "Couldn't start Maharaj Ji."
        );
    }
}


// =====================================================
// HANDLE LIVE MESSAGE
// =====================================================

function handleLiveMessage(event) {

    if (endingConversation) return;

    try {

        let raw = event.data;

        if (raw instanceof Blob) {

            raw.text().then(
                text =>
                    handleLiveMessage({
                        data: text
                    })
            );

            return;
        }

        if (raw instanceof ArrayBuffer) {

            raw =
                new TextDecoder().decode(
                    new Uint8Array(raw)
                );
        }

        const message =
            JSON.parse(raw);

        console.log(
            "GEMINI LIVE:",
            message
        );

        // SETUP
        if (message.setupComplete) {

            setupComplete = true;

            console.log(
                "SETUP COMPLETE"
            );

            if (voiceMode) {

                setState(
                    "listening",
                    "I'm listening..."
                );

                startMicrophone();

            } else {

                setState(
                    "",
                    "Type your next message."
                );
            }

            const queued =
                pendingTextMessages.splice(0);

            for (const text of queued) {
                sendTextToLive(text);
            }

            return;
        }

        // TOOL CALL
        if (message.toolCall) {

            handleToolCall(
                message.toolCall
            );

            return;
        }

        const content =
            message.serverContent;

        if (!content) return;

        // INTERRUPTION
        if (content.interrupted) {

            console.log(
                "USER INTERRUPTED MAHARAJ JI"
            );

            stopAudio();

            if (
                maharajActive &&
                voiceMode &&
                !endingConversation
            ) {

                setState(
                    "listening",
                    "I'm listening..."
                );

                startMicrophone();
            }
        }

        // USER TRANSCRIPTION
        if (content.inputTranscription) {

            const transcript =
                (
                    content.inputTranscription.text ||
                    ""
                ).trim();

            if (transcript) {

                console.log(
                    "USER:",
                    transcript
                );

                // EMERGENCY: save confirmed meal directly
                // ==========================================
// SAVE CONFIRMED MEAL
// ==========================================

const confirmationText =
    transcript.toLowerCase();

const isMealConfirmation =
    confirmationText.includes("cook this") ||
    confirmationText.includes("make this") ||
    confirmationText.includes("go with this") ||
    confirmationText.includes("this sounds good") ||
    confirmationText.includes("yes, i'll") ||
    confirmationText.includes("yes i'll");

if (
    isMealConfirmation &&
    lastRecommendedMealText
) {

    console.log(
        "CONFIRMED MEAL:",
        lastRecommendedMealText
    );

    fetch("/api/chat", {
        method: "POST",

        headers: {
            "Content-Type":
                "application/json"
        },

        body: JSON.stringify({

            message: transcript,

            live_meal: {

                name:
                lastRecommendedMealText
        .split(/[.!?]/)[0]
        .replace(
            /^how about\s+(a|an|the)\s+/i,
            ""
        )
        .replace(
            /^you could make\s+(a|an|the)\s+/i,
            ""
        )
        .trim(),

                reason:
                    "Meal recommended and confirmed during conversation.",

                description:
                    lastRecommendedMealText,

                ingredients: [],

                preparation_time: 0,

                estimated_cost: 0
            }
        })
    })
    .then(response =>
        response.json()
    )
    .then(data => {

        console.log(
            "CONFIRMED MEAL SAVED:",
            data
        );

    })
    .catch(error => {

        console.error(
            "CONFIRMED MEAL SAVE ERROR:",
            error
        );

    });
}


                if (
                    isExplicitStopRequest(
                        transcript
                    )
                ) {

                    console.log(
                        "STOP COMMAND DETECTED:",
                        transcript
                    );

                    endConversationImmediately();
                    return;
                }

                if (!currentUserBubble) {

                    currentUserBubble =
                        addMessage(
                            transcript,
                            "user"
                        );

                } else {

                    appendBubbleText(
                        currentUserBubble,
                        transcript
                    );
                }
            }
        }

        // MODEL TRANSCRIPTION
        if (content.outputTranscription) {

            const transcript =
                (
                    content.outputTranscription.text ||
                    ""
                );

            if (transcript) {

                console.log(
                    "MAHARAJ JI:",
                    transcript
                );
                lastRecommendedMealText += transcript;

                if (!currentAssistantBubble) {

                    currentAssistantBubble =
                        addMessage(
                            transcript,
                            "assistant"
                        );

                } else {

                    appendBubbleText(
                        currentAssistantBubble,
                        transcript
                    );
                }
            }
        }

        // MODEL AUDIO
        if (
            content.modelTurn &&
            content.modelTurn.parts
        ) {

            if (!maharajActive) return;

            if (voiceMode) {

                setState(
                    "speaking",
                    "Maharaj Ji is speaking..."
                );

                for (
                    const part of
                    content.modelTurn.parts
                ) {

                    if (
                        part.inlineData &&
                        part.inlineData.data
                    ) {

                        queueAudio(
                            part.inlineData.data
                        );
                    }
                }
            }
        }

        // TURN COMPLETE
        if (content.turnComplete) {

            console.log(
                "TURN COMPLETE"
            );

            currentUserBubble = null;
            currentAssistantBubble = null;

            if (
                !maharajActive ||
                endingConversation
            ) {
                return;
            }

            // IMPORTANT:
            // turnComplete DOES NOT end the conversation.

            if (voiceMode) {

                setState(
                    "listening",
                    "I'm listening..."
                );

                startMicrophone();

            } else {

                setState(
                    "",
                    "Type your next message."
                );
            }
        }

    } catch (error) {

        console.error(
            "LIVE MESSAGE ERROR:",
            error
        );
    }
}


// =====================================================
// TOOL CALL
// =====================================================

async function handleToolCall(toolCall) {

    if (
        !maharajActive ||
        endingConversation
    ) {
        return;
    }

    console.log(
        "MAHARAJ JI TOOL CALL:",
        toolCall
    );

    stopMicrophone();

    setState(
        "thinking",
        "Maharaj Ji is thinking..."
    );

    const functionResponses = [];

    for (
        const functionCall of
        (toolCall.functionCalls || [])
    ) {

        if (
            !maharajActive ||
            endingConversation
        ) {
            return;
        }

        console.log(
            "FUNCTION:",
            functionCall.name
        );

        console.log(
            "ARGS:",
            functionCall.args
        );

        if (
            functionCall.name ===
            "run_food_agent"
        ) {
            const userMessage =
    functionCall
        .args
        ?.user_message || "";

const recommendedMeal =
    functionCall
        .args
        ?.recommended_meal || null;

console.log(
    "RECOMMENDED MEAL FROM LIVE:",
    recommendedMeal
);

const result =
    await runFoodAgentTool(
        userMessage,
        recommendedMeal
    );

            if (
                !maharajActive ||
                endingConversation
            ) {
                return;
            }

            functionResponses.push({

                name:
                    functionCall.name,

                id:
                    functionCall.id,

                response: {
                    result: result
                }
            });
        }
    }

    if (
        socket &&
        socket.readyState === WebSocket.OPEN &&
        maharajActive &&
        !endingConversation &&
        functionResponses.length > 0
    ) {

        socket.send(
            JSON.stringify({

                toolResponse: {

                    functionResponses:
                        functionResponses
                }
            })
        );

        console.log(
            "FOOD AGENT RESULT SENT BACK TO LIVE"
        );
    }
}


// =====================================================
// FOOD BACKEND TOOL
// =====================================================

async function runFoodAgentTool(
    userMessage,
    recommendedMeal = null
) {

    console.log(
        "FOOD AGENT TOOL CALLED:",
        userMessage
    );

    console.log(
        "LIVE RECOMMENDED MEAL:",
        recommendedMeal
    );

    try {

        const response =
            await fetch(
                "/api/chat",
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body:
                        JSON.stringify({

                            message:
                                userMessage,

                            live_meal:
                                recommendedMeal

                        })
                }
            );

        const data =
            await response.json();

        if (
            !response.ok ||
            !data.success
        ) {

            throw new Error(
                data.error ||
                "Food agent request failed."
            );

        }

        console.log(
            "FOOD AGENT RESULT:",
            data.result
        );

        return data.result;

    } catch (error) {

        console.error(
            "FOOD AGENT TOOL ERROR:",
            error
        );

        return {

            status: "ERROR",

            message:
                "I couldn't complete the meal planning request right now."

        };
    }
}


// =====================================================
// TEXT → SAME LIVE BRAIN
// =====================================================

async function sendTextMessage() {

    if (!messageInput) return;

    const message =
        messageInput.value.trim();

    if (!message) return;

    messageInput.value = "";

    // STOP FROM TEXT
    if (
        isExplicitStopRequest(message)
    ) {

        addMessage(
            message,
            "user"
        );

        endConversationImmediately();

        return;
    }

    addMessage(
        message,
        "user"
    );

    currentUserBubble = null;
    currentAssistantBubble = null;

    // SAME ACTIVE LIVE SESSION
    if (
        socket &&
        socket.readyState === WebSocket.OPEN &&
        setupComplete &&
        maharajActive
    ) {

        sendTextToLive(message);
        return;
    }

// -----------------------------------------------------
// CREATE TEXT LIVE SESSION
// -----------------------------------------------------

maharajActive =
    true;

waitingForWakeWord =
    false;

endingConversation =
    false;

// Text and Kitchen actions should enter the same
// active voice conversation. This means Maharaj Ji
// can speak the answer and keep listening afterwards.
voiceMode =
    true;

stopWakeWordListener();

pendingTextMessages.push(
    message
);

await createLiveSession();
}


// =====================================================
// SEND TEXT INTO SAME LIVE SESSION
// =====================================================

function sendTextToLive(text) {

    if (
        !socket ||
        socket.readyState !== WebSocket.OPEN
    ) {

        pendingTextMessages.push(text);
        return;
    }

    console.log(
        "TEXT → SAME LIVE SESSION:",
        text
    );

    setState(
        "thinking",
        "Maharaj Ji is thinking..."
    );

    socket.send(
        JSON.stringify({

            clientContent: {

                turns: [
                    {
                        role: "user",

                        parts: [
                            {
                                text: text
                            }
                        ]
                    }
                ],

                turnComplete: true
            }
        })
    );
}


// =====================================================
// STOP CONVERSATION
// =====================================================

function endConversationImmediately() {

    console.log(
        "MAHARAJ JI STOPPED BY USER"
    );

    endingConversation = true;

    maharajActive = false;
    waitingForWakeWord = true;
    voiceMode = false;
    setupComplete = false;

    pendingTextMessages = [];

    currentUserBubble = null;
    currentAssistantBubble = null;

    stopMicrophone();
    stopAudio();
    stopWakeWordListener();

    if (socket) {

        try {

            if (
                socket.readyState ===
                    WebSocket.OPEN ||

                socket.readyState ===
                    WebSocket.CONNECTING
            ) {

                socket.close(
                    1000,
                    "User ended conversation"
                );
            }

        } catch (error) {

            console.log(
                "Socket close error:",
                error
            );
        }
    }

    socket = null;

    setState(
        "",
        'Say "Hi Maharaj Ji" to wake me.'
    );

    setTimeout(
        () => {

            endingConversation = false;

            startWakeWordListener();

        },
        500
    );
}


// =====================================================
// STOP COMMAND DETECTION
// =====================================================

function isExplicitStopRequest(text) {

    if (!text) return false;

    const normalized =
        text
            .toLowerCase()
            .replace(/[.,!?]/g, " ")
            .replace(/\s+/g, " ")
            .trim();

    const directStopPatterns = [

        // English
        /^stop$/,
        /^okay stop$/,
        /^ok stop$/,
        /^stop now$/,
        /^you can stop$/,
        /^you can stop now$/,
        /^stop talking$/,
        /^stop speaking$/,
        /^please stop$/,
        /^okay please stop$/,
        /^ok please stop$/,

        /^keep quiet$/,
        /^please keep quiet$/,
        /^okay keep quiet$/,
        /^ok keep quiet$/,
        /^be quiet$/,
        /^please be quiet$/,

        /^that's enough$/,
        /^thats enough$/,
        /^okay that's enough$/,
        /^okay thats enough$/,

        /^that's all$/,
        /^thats all$/,
        /^that's it$/,
        /^thats it$/,
        /^that's it for now$/,
        /^thats it for now$/,

        /^we are done$/,
        /^we're done$/,
        /^okay we're done$/,
        /^ok we're done$/,

        /^goodbye$/,
        /^good bye$/,
        /^bye$/,
        /^bye for now$/,

        /^see you later$/,
        /^talk to you later$/,

        /^continue later$/,
        /^we'll continue later$/,
        /^we will continue later$/,

        /^i don't need anything else$/,
        /^i do not need anything else$/,

        // Hinglish
        /^bas$/,
        /^bas karo$/,
        /^bas kar do$/,
        /^band karo$/,
        /^ab bas$/,
        /^ab bas karo$/,
        /^theek hai bas$/,
        /^thik hai bas$/,

        /^chup$/,
        /^chup raho$/,
        /^chup karo$/,
        /^chup ho jao$/,
        /^chup reh$/,

        /^shant raho$/,
        /^shaant raho$/,
        /^shant ho jao$/,
        /^shaant ho jao$/,

        /^mujhe aur kuch nahi chahiye$/,
        /^itna hi$/,
        /^itna hi chahiye$/,

        // Hindi
        /^चुप$/,
        /^चुप रहो$/,
        /^चुप करो$/,
        /^चुप हो जाओ$/,
        /^शांत रहो$/,
        /^शांत हो जाओ$/,
        /^बस$/,
        /^बस करो$/,
        /^अब बस$/,
        /^बंद करो$/,
        /^बोलना बंद करो$/,
        /^इतना ही$/,
        /^मुझे और कुछ नहीं चाहिए$/
    ];

    if (
        directStopPatterns.some(
            pattern => pattern.test(normalized)
        )
    ) {
        return true;
    }

    const hasStopWord =
        /\bstop\b/.test(normalized) ||
        /\bstopped\b/.test(normalized);

    const hasQuietIntent =
        normalized.includes("keep quiet") ||
        normalized.includes("be quiet") ||
        normalized.includes("chup") ||
        normalized.includes("chup raho") ||
        normalized.includes("chup karo") ||
        normalized.includes("chup ho jao") ||
        normalized.includes("shant raho") ||
        normalized.includes("shaant raho") ||
        normalized.includes("shant ho jao") ||
        normalized.includes("shaant ho jao") ||
        normalized.includes("band karo") ||
        normalized.includes("bolna band karo") ||
        normalized.includes("चुप") ||
        normalized.includes("शांत") ||
        normalized.includes("बस करो") ||
        normalized.includes("बंद करो");

    const hasEndingIntent =
        normalized.includes("that's enough") ||
        normalized.includes("thats enough") ||
        normalized.includes("that's all") ||
        normalized.includes("thats all") ||
        normalized.includes("that's it") ||
        normalized.includes("thats it") ||
        normalized.includes("we are done") ||
        normalized.includes("we're done") ||
        normalized.includes("goodbye") ||
        normalized.includes("bye for now") ||
        normalized.includes("continue later") ||
        normalized.includes("don't need anything else") ||
        normalized.includes("do not need anything else");

    const explicitlySaysDontStop =
        normalized.includes("don't stop") ||
        normalized.includes("do not stop");

    if (
        !explicitlySaysDontStop &&
        (
            hasStopWord ||
            hasQuietIntent ||
            hasEndingIntent
        )
    ) {
        return true;
    }

    return false;
}


// =====================================================
// WAKE WORD LISTENER
// =====================================================

function startWakeWordListener() {

    if (
        maharajActive ||
        wakeRecognitionRunning
    ) {
        return;
    }

    const SpeechRecognition =
        window.SpeechRecognition ||
        window.webkitSpeechRecognition;

    if (!SpeechRecognition) {

        setState(
            "",
            'Chrome is required for "Hi Maharaj Ji".'
        );

        return;
    }

    wakeRecognition =
        new SpeechRecognition();

    wakeRecognition.continuous = true;
    wakeRecognition.interimResults = true;
    wakeRecognition.lang = "en-IN";

    wakeRecognition.onstart = () => {

        wakeRecognitionRunning = true;
        waitingForWakeWord = true;

        setState(
            "",
            'Say "Hi Maharaj Ji" to wake me.'
        );
    };

    wakeRecognition.onresult = (event) => {

        let transcript = "";

        for (
            let i = event.resultIndex;
            i < event.results.length;
            i++
        ) {
            transcript +=
                event.results[i][0].transcript;
        }

        transcript =
            transcript.toLowerCase().trim();

        if (!transcript) return;

        console.log(
            "WAKE LISTENER:",
            transcript
        );

        const wakePhrases = [
            "hi maharaj ji",
            "hey maharaj ji",
            "hello maharaj ji",
            "maharaj ji"
        ];

        const detected =
            wakePhrases.some(
                phrase =>
                    transcript.includes(phrase)
            );

        if (
            detected &&
            !maharajActive
        ) {

            console.log(
                "MAHARAJ JI WOKEN"
            );

            maharajActive = true;
            waitingForWakeWord = false;
            endingConversation = false;
            voiceMode = true;

            stopWakeWordListener();

            setState(
                "thinking",
                "Starting Maharaj Ji..."
            );

            createLiveSession();
        }
    };

    wakeRecognition.onerror = (event) => {

        console.log(
            "WAKE ERROR:",
            event.error
        );

        wakeRecognitionRunning = false;

        if (
            event.error ===
            "not-allowed"
        ) {

            setState(
                "",
                "Microphone permission is required."
            );

            return;
        }

        if (!maharajActive) {

            setTimeout(
                startWakeWordListener,
                1000
            );
        }
    };

    wakeRecognition.onend = () => {

        wakeRecognitionRunning = false;

        if (
            !maharajActive &&
            waitingForWakeWord &&
            !endingConversation
        ) {

            setTimeout(
                startWakeWordListener,
                500
            );
        }
    };

    try {

        wakeRecognition.start();

    } catch (error) {

        console.log(
            "Wake listener start skipped."
        );
    }
}


// =====================================================
// STOP WAKE LISTENER
// =====================================================

function stopWakeWordListener() {

    if (wakeRecognition) {

        try {
            wakeRecognition.stop();
        } catch (error) {}
    }

    wakeRecognition = null;
    wakeRecognitionRunning = false;
}


// =====================================================
// MICROPHONE
// =====================================================

async function startMicrophone() {

    if (
        microphoneStream ||
        !maharajActive ||
        !voiceMode ||
        endingConversation
    ) {
        return;
    }

    if (
        !socket ||
        socket.readyState !== WebSocket.OPEN
    ) {
        return;
    }

    try {

        microphoneStream =
            await navigator.mediaDevices.getUserMedia({
                audio: {
                    channelCount: 1,
                    echoCancellation: true,
                    noiseSuppression: true,
                    autoGainControl: true
                }
            });

        audioContext =
            new (
                window.AudioContext ||
                window.webkitAudioContext
            )();

        await audioContext.resume();

        microphoneSource =
            audioContext.createMediaStreamSource(
                microphoneStream
            );

        processor =
            audioContext.createScriptProcessor(
                2048,
                1,
                1
            );

        processor.onaudioprocess =
            (event) => {

                if (
                    !maharajActive ||
                    endingConversation ||
                    !socket ||
                    socket.readyState !== WebSocket.OPEN
                ) {
                    return;
                }

                const input =
                    event.inputBuffer.getChannelData(0);

                const pcm =
                    downsampleTo16k(
                        input,
                        audioContext.sampleRate
                    );

                socket.send(
                    JSON.stringify({
                        realtimeInput: {
                            audio: {
                                data:
                                    int16ToBase64(pcm),
                                mimeType:
                                    "audio/pcm;rate=16000"
                            }
                        }
                    })
                );
            };

        microphoneSource.connect(processor);
        processor.connect(audioContext.destination);

        console.log(
            "MICROPHONE ACTIVE"
        );

    } catch (error) {

        console.error(
            "MICROPHONE ERROR:",
            error
        );

        maharajActive = false;
        waitingForWakeWord = true;

        stopMicrophone();
        startWakeWordListener();
    }
}


function stopMicrophone() {

    if (processor) {

        processor.onaudioprocess = null;

        try {
            processor.disconnect();
        } catch (error) {}

        processor = null;
    }

    if (microphoneSource) {

        try {
            microphoneSource.disconnect();
        } catch (error) {}

        microphoneSource = null;
    }

    if (microphoneStream) {

        microphoneStream
            .getTracks()
            .forEach(
                track => track.stop()
            );

        microphoneStream = null;
    }

    if (audioContext) {

        try {
            audioContext.close();
        } catch (error) {}

        audioContext = null;
    }
}


// =====================================================
// AUDIO HELPERS
// =====================================================

function downsampleTo16k(
    input,
    inputSampleRate
) {

    const targetSampleRate = 16000;

    if (
        inputSampleRate ===
        targetSampleRate
    ) {
        return floatTo16BitPCM(input);
    }

    const ratio =
        inputSampleRate /
        targetSampleRate;

    const newLength =
        Math.round(
            input.length /
            ratio
        );

    const result =
        new Int16Array(newLength);

    for (
        let i = 0;
        i < newLength;
        i++
    ) {

        const index =
            Math.floor(i * ratio);

        let sample =
            input[index];

        sample =
            Math.max(
                -1,
                Math.min(1, sample)
            );

        result[i] =
            sample < 0
                ? sample * 32768
                : sample * 32767;
    }

    return result;
}


function floatTo16BitPCM(input) {

    const output =
        new Int16Array(
            input.length
        );

    for (
        let i = 0;
        i < input.length;
        i++
    ) {

        let sample =
            Math.max(
                -1,
                Math.min(
                    1,
                    input[i]
                )
            );

        output[i] =
            sample < 0
                ? sample * 32768
                : sample * 32767;
    }

    return output;
}


function int16ToBase64(pcm) {

    const bytes =
        new Uint8Array(
            pcm.buffer
        );

    let binary = "";
    const chunkSize = 0x8000;

    for (
        let i = 0;
        i < bytes.length;
        i += chunkSize
    ) {

        binary +=
            String.fromCharCode(
                ...bytes.subarray(
                    i,
                    Math.min(
                        i + chunkSize,
                        bytes.length
                    )
                )
            );
    }

    return btoa(binary);
}


// =====================================================
// AUDIO PLAYBACK
// =====================================================

function queueAudio(base64) {

    if (
        endingConversation ||
        !maharajActive ||
        !voiceMode
    ) {
        return;
    }

    audioQueue.push(base64);

    if (!isPlaying) {
        playNextAudio();
    }
}


function playNextAudio() {

    if (!audioQueue.length) {

        isPlaying = false;
        return;
    }

    if (!audioContext) {

        audioQueue = [];
        isPlaying = false;
        return;
    }

    if (
        endingConversation ||
        !maharajActive ||
        !voiceMode
    ) {

        audioQueue = [];
        isPlaying = false;
        return;
    }

    isPlaying = true;

    const base64 =
        audioQueue.shift();

    const binary = atob(base64);

    const bytes =
        new Uint8Array(
            binary.length
        );

    for (
        let i = 0;
        i < binary.length;
        i++
    ) {
        bytes[i] =
            binary.charCodeAt(i);
    }

    const pcm =
        new Int16Array(
            bytes.buffer
        );

    const buffer =
        audioContext.createBuffer(
            1,
            pcm.length,
            24000
        );

    const channel =
        buffer.getChannelData(0);

    for (
        let i = 0;
        i < pcm.length;
        i++
    ) {
        channel[i] =
            pcm[i] / 32768;
    }

    const source =
        audioContext.createBufferSource();

    source.buffer = buffer;

    source.connect(
        audioContext.destination
    );

    const startTime =
        Math.max(
            audioContext.currentTime,
            nextAudioTime
        );

    nextAudioTime =
        startTime +
        buffer.duration;

    currentAudioSource = source;

    source.onended = () => {

        if (
            currentAudioSource ===
            source
        ) {
            currentAudioSource = null;
        }

        isPlaying = false;
        playNextAudio();
    };

    source.start(startTime);
}


function stopAudio() {

    audioQueue = [];

    if (audioContext) {
        nextAudioTime =
            audioContext.currentTime;
    } else {
        nextAudioTime = 0;
    }

    if (currentAudioSource) {

        try {
            currentAudioSource.stop();
        } catch (error) {}

        currentAudioSource = null;
    }

    isPlaying = false;
}


// =====================================================
// UI EVENTS
// =====================================================

if (sendButton) {

    sendButton.addEventListener(
        "click",
        sendTextMessage
    );
}

if (messageInput) {

    messageInput.addEventListener(
        "keydown",
        event => {

            if (
                event.key ===
                "Enter"
            ) {
                sendTextMessage();
            }
        }
    );
}


// =====================================================
// APPLICATION START
// =====================================================

window.addEventListener(
    "load",
    () => {

        console.log(
            "================================"
        );

        console.log(
            "MAHARAJ JI"
        );

        console.log(
            "SAME BRAIN FOR VOICE + TEXT"
        );

        console.log(
            "================================"
        );

        setState(
            "",
            'Say "Hi Maharaj Ji" to wake me.'
        );

        startWakeWordListener();
    }
);