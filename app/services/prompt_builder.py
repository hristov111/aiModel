"""Prompt builder for constructing system prompts with memory injection."""

from typing import List, Dict, Optional
from datetime import datetime

from app.models.memory import Memory, Message
from app.core.config import settings


class PromptBuilder:
    """Builds prompts for the LLM with persona, memories, and conversation history."""
    
    def __init__(self, persona: Optional[str] = None):
        """
        Initialize prompt builder.
        
        Args:
            persona: System persona description (defaults to config)
        """
        self.persona = persona or settings.system_persona
    
    def build_system_prompt(
        self,
        relevant_memories: List[Memory],
        conversation_summary: Optional[str] = None,
        user_preferences: Optional[Dict] = None,
        detected_emotion: Optional[Dict] = None,
        emotion_context: Optional[Dict] = None,
        personality_config: Optional[Dict] = None,
        relationship_state: Optional[Dict] = None,
        goal_context: Optional[Dict] = None
    ) -> str:
        """
        Build the system prompt with persona, personality, memory, preferences, emotional awareness, and goals.
        
        Args:
            relevant_memories: List of relevant memories to include
            conversation_summary: Optional conversation summary
            user_preferences: User's communication preferences (HARD ENFORCEMENT)
            detected_emotion: Current detected emotion {emotion, confidence, intensity}
            emotion_context: Emotion trend analysis {dominant_emotion, recent_trend, needs_attention}
            personality_config: AI personality configuration
            relationship_state: Relationship metrics and history
            goal_context: User's goals and progress tracking
            
        Returns:
            Complete system prompt string
        """
        prompt_parts = []
        
        # Add persona with personality overlay
        base_persona = self._build_personality_persona(personality_config, user_preferences)
        prompt_parts.append(base_persona)
        
        # Add memories if available
        if relevant_memories:
            prompt_parts.append("\nRelevant memories from past conversations:")
            for idx, memory in enumerate(relevant_memories, 1):
                memory_text = f"- {memory.content}"
                if memory.memory_type:
                    memory_text += f" ({memory.memory_type.value})"
                prompt_parts.append(memory_text)
        
        # Add conversation summary if available
        if conversation_summary:
            prompt_parts.append(f"\nRecent conversation summary:")
            prompt_parts.append(conversation_summary)
        
        # Add PERSONALITY TRAITS & BEHAVIORS
        if personality_config:
            personality_instructions = self._build_personality_instructions(personality_config, relationship_state)
            if personality_instructions:
                prompt_parts.append("\n🎭 YOUR PERSONALITY & ROLE:")
                prompt_parts.extend(personality_instructions)
        
        # Add EMOTION-AWARE INSTRUCTIONS (context-based empathy)
        if detected_emotion or emotion_context:
            emotion_instructions = self._build_emotion_instructions(detected_emotion, emotion_context)
            if emotion_instructions:
                prompt_parts.append("\n💭 EMOTIONAL CONTEXT & RESPONSE GUIDANCE:")
                prompt_parts.extend(emotion_instructions)
        
        # Add GOALS & PROGRESS TRACKING
        if goal_context:
            goal_instructions = self._build_goal_instructions(goal_context)
            if goal_instructions:
                prompt_parts.append("\n🎯 USER'S GOALS & PROGRESS:")
                prompt_parts.extend(goal_instructions)
        
        # Add HARD ENFORCED communication preferences
        if user_preferences:
            pref_instructions = self._build_preference_instructions(user_preferences)
            if pref_instructions:
                prompt_parts.append("\n⚠️ CRITICAL COMMUNICATION REQUIREMENTS (MUST FOLLOW):")
                prompt_parts.extend(pref_instructions)
        
        # Add general instructions
        prompt_parts.append("\nGeneral Instructions:")
        prompt_parts.append("- Be helpful and conversational")
        prompt_parts.append("- Reference relevant memories naturally when appropriate")
        prompt_parts.append("- Remember context from this conversation")
        prompt_parts.append("- If you don't know something, be honest about it")
        
        return "\n".join(prompt_parts)
    
    def _adapt_persona_for_language(self, user_preferences: Optional[Dict]) -> str:
        """Adapt base persona based on language preference."""
        if not user_preferences:
            return self.persona
        
        language = user_preferences.get('language', '').lower()
        
        # Language-specific persona translations
        language_personas = {
            'spanish': 'un asistente de IA útil y con conocimientos, con memoria de conversaciones pasadas',
            'french': 'un assistant IA utile et compétent avec mémoire des conversations passées',
            'german': 'ein hilfreicher und sachkundiger KI-Assistent mit Gedächtnis vergangener Gespräche',
            'italian': 'un assistente AI utile e competente con memoria delle conversazioni passate',
            'portuguese': 'um assistente de IA útil e experiente com memória de conversas anteriores',
        }
        
        return language_personas.get(language, self.persona)
    
    def _build_preference_instructions(self, user_preferences: Dict) -> List[str]:
        """Build hard-enforced instructions from user preferences."""
        instructions = []
        
        # Language enforcement
        language = user_preferences.get('language')
        if language and language.lower() != 'english':
            instructions.append(f"🌐 LANGUAGE: You MUST respond ENTIRELY in {language.title()}. Do not use English unless specifically requested.")
        
        # Formality enforcement
        formality = user_preferences.get('formality')
        if formality == 'casual':
            instructions.append("💬 FORMALITY: Use casual, informal language. Use contractions (you're, I'm, don't). Be relaxed and friendly.")
        elif formality == 'formal':
            instructions.append("👔 FORMALITY: Use formal, polite language. Avoid contractions. Maintain professional tone at all times.")
        elif formality == 'professional':
            instructions.append("💼 FORMALITY: Use professional business language. Be polite, respectful, and maintain corporate standards.")
        
        # Tone enforcement
        tone = user_preferences.get('tone')
        if tone == 'enthusiastic':
            instructions.append("⚡ TONE: Be enthusiastic and energetic! Show excitement and positivity in every response!")
        elif tone == 'calm':
            instructions.append("🧘 TONE: Maintain a calm, measured, and relaxed tone. Be steady and composed.")
        elif tone == 'friendly':
            instructions.append("😊 TONE: Be warm, friendly, and welcoming. Make the user feel comfortable.")
        elif tone == 'neutral':
            instructions.append("⚖️ TONE: Remain neutral and objective. Avoid emotional language.")
        
        # Emoji enforcement
        emoji_usage = user_preferences.get('emoji_usage')
        if emoji_usage is True:
            instructions.append("😀 EMOJIS: Include relevant emojis in your responses to add personality and clarity.")
        elif emoji_usage is False:
            instructions.append("🚫 EMOJIS: Do NOT use any emojis. Keep responses text-only.")
        
        # Response length enforcement
        response_length = user_preferences.get('response_length')
        if response_length == 'brief':
            instructions.append("📏 LENGTH: Keep responses BRIEF and CONCISE. 2-3 sentences maximum unless more detail is absolutely necessary.")
        elif response_length == 'detailed':
            instructions.append("📚 LENGTH: Provide DETAILED and THOROUGH responses. Include examples, explanations, and comprehensive coverage.")
        elif response_length == 'balanced':
            instructions.append("⚖️ LENGTH: Provide balanced responses - not too short, not too long. Be comprehensive but concise.")
        
        # Explanation style enforcement
        explanation_style = user_preferences.get('explanation_style')
        if explanation_style == 'simple':
            instructions.append("🎓 STYLE: Explain everything in SIMPLE terms. Assume no prior knowledge. Use everyday language, not jargon.")
        elif explanation_style == 'technical':
            instructions.append("🔬 STYLE: Use TECHNICAL language and terminology. Include technical details and precise explanations.")
        elif explanation_style == 'analogies':
            instructions.append("🌟 STYLE: Use ANALOGIES and METAPHORS to explain concepts. Compare to familiar things.")
        
        return instructions
    
    def _build_emotion_instructions(
        self, 
        detected_emotion: Optional[Dict], 
        emotion_context: Optional[Dict]
    ) -> List[str]:
        """Build emotion-aware response instructions."""
        instructions = []
        
        # Define emotion-specific response strategies
        emotion_strategies = {
            'sad': {
                'approach': 'supportive_empathetic',
                'instructions': [
                    "The user is feeling sad. Be gentle, supportive, and empathetic.",
                    "Acknowledge their feelings without dismissing them.",
                    "Offer comfort and show that you understand.",
                    "Avoid being overly cheerful - meet them where they are emotionally."
                ]
            },
            'angry': {
                'approach': 'calm_deescalating',
                'instructions': [
                    "The user is angry. Stay calm and professional.",
                    "Validate their feelings without inflaming the situation.",
                    "Be solution-focused and avoid defensive language.",
                    "Don't take it personally - help them work through the issue."
                ]
            },
            'frustrated': {
                'approach': 'patient_supportive',
                'instructions': [
                    "The user is frustrated. Be patient and understanding.",
                    "Break down complex issues into manageable steps.",
                    "Offer clear, structured solutions.",
                    "Acknowledge that frustration is normal when facing challenges."
                ]
            },
            'anxious': {
                'approach': 'calm_reassuring',
                'instructions': [
                    "The user is anxious or worried. Provide calm reassurance.",
                    "Break information into clear, manageable pieces.",
                    "Avoid overwhelming them with too much at once.",
                    "Offer practical steps they can take to feel more in control."
                ]
            },
            'happy': {
                'approach': 'warm_positive',
                'instructions': [
                    "The user is happy! Match their positive energy.",
                    "Be warm and enthusiastic in your response.",
                    "Share in their joy and celebrate with them.",
                    "Keep the conversation uplifting and positive."
                ]
            },
            'excited': {
                'approach': 'enthusiastic_celebratory',
                'instructions': [
                    "The user is excited! Share their enthusiasm!",
                    "Be energetic and celebratory in your response.",
                    "Amplify their excitement - this is a great moment for them!",
                    "Use exclamation points and positive language to match their energy."
                ]
            },
            'grateful': {
                'approach': 'warm_humble',
                'instructions': [
                    "The user is expressing gratitude. Be warm and gracious.",
                    "Accept their thanks humbly - you're here to help.",
                    "Reinforce that you're happy to assist anytime.",
                    "Keep the tone positive and encouraging."
                ]
            },
            'confused': {
                'approach': 'clear_patient',
                'instructions': [
                    "The user is confused. Provide clear, simple explanations.",
                    "Break down complex concepts into digestible pieces.",
                    "Use examples and analogies to clarify.",
                    "Check for understanding before moving forward."
                ]
            },
            'disappointed': {
                'approach': 'encouraging_supportive',
                'instructions': [
                    "The user is disappointed. Be supportive and encouraging.",
                    "Acknowledge the disappointment without minimizing it.",
                    "Help them see alternative paths or solutions.",
                    "Remind them that setbacks are temporary and growth opportunities."
                ]
            },
            'proud': {
                'approach': 'celebratory_affirming',
                'instructions': [
                    "The user is proud of an accomplishment! Celebrate with them!",
                    "Recognize their hard work and success.",
                    "Be genuinely happy for them and affirm their achievement.",
                    "Encourage them to keep up the great work."
                ]
            },
            'lonely': {
                'approach': 'warm_companionable',
                'instructions': [
                    "The user is feeling lonely. Be warm and present.",
                    "Engage meaningfully - show genuine interest in them.",
                    "Remind them that their feelings are valid.",
                    "Be a companion in conversation - you're here with them."
                ]
            },
            'hopeful': {
                'approach': 'encouraging_optimistic',
                'instructions': [
                    "The user is feeling hopeful. Nurture that optimism!",
                    "Be encouraging and support their positive outlook.",
                    "Help them build on their hope with practical steps.",
                    "Share in their optimism while staying grounded."
                ]
            }
        }
        
        # Current emotion response
        if detected_emotion:
            emotion = detected_emotion.get('emotion')
            confidence = detected_emotion.get('confidence', 0)
            intensity = detected_emotion.get('intensity', 'medium')
            
            if emotion in emotion_strategies and confidence > 0.5:
                strategy = emotion_strategies[emotion]
                instructions.append(f"📊 DETECTED EMOTION: {emotion.title()} (confidence: {confidence:.0%}, intensity: {intensity})")
                instructions.extend([f"  {inst}" for inst in strategy['instructions']])
        
        # Emotion trend context
        if emotion_context:
            dominant = emotion_context.get('dominant_emotion')
            trend = emotion_context.get('recent_trend')
            needs_attention = emotion_context.get('needs_attention', False)
            
            if dominant and trend:
                instructions.append(f"📈 EMOTION PATTERN: User has been mostly {dominant} recently (trend: {trend})")
                
                if needs_attention:
                    instructions.append("  ⚠️ ATTENTION: User has shown multiple negative emotions recently.")
                    instructions.append("  Be extra supportive and check in on their wellbeing if appropriate.")
                
                # Trend-specific guidance
                if trend == 'improving':
                    instructions.append("  ✅ Good news: Their emotional state is improving. Acknowledge progress!")
                elif trend == 'declining':
                    instructions.append("  ⚠️ Their emotional state may be declining. Be extra sensitive and supportive.")
        
        return instructions
    
    def _build_personality_persona(
        self,
        personality_config: Optional[Dict],
        user_preferences: Optional[Dict]
    ) -> str:
        """Build the core persona with personality and preferences."""
        if not personality_config:
            # Default persona
            base_persona = self._adapt_persona_for_language(user_preferences)
            return f"You are {base_persona}."
        
        # Get personality info
        archetype = personality_config.get('archetype')
        relationship_type = personality_config.get('relationship_type', 'assistant')
        custom_instructions = personality_config.get('custom', {}).get('custom_instructions')
        backstory = personality_config.get('custom', {}).get('backstory')
        
        # Build persona description
        persona_parts = []
        
        if archetype:
            # Map archetype to persona description
            archetype_personas = {
                'wise_mentor': 'a wise mentor who guides with experience and wisdom',
                'supportive_friend': 'a warm, supportive friend who listens without judgment',
                'professional_coach': 'a professional coach focused on goals and results',
                'creative_partner': 'an imaginative creative partner who loves exploring ideas',
                'calm_therapist': 'a calm, patient therapist who creates a safe space',
                'enthusiastic_cheerleader': 'an enthusiastic cheerleader who celebrates every win',
                'pragmatic_advisor': 'a pragmatic advisor who gives straightforward advice',
                'curious_student': 'a curious learner who explores topics deeply',
                'balanced_companion': 'a balanced AI companion who adapts to your needs'
            }
            persona_parts.append(f"You are {archetype_personas.get(archetype, 'a helpful AI assistant')}.")
        else:
            persona_parts.append(f"You are a helpful AI {relationship_type}.")
        
        # Add backstory if provided
        if backstory:
            persona_parts.append(f"\nYour context: {backstory}")
        
        # Add custom instructions
        if custom_instructions:
            persona_parts.append(f"\nSpecial instructions: {custom_instructions}")
        
        return "\n".join(persona_parts)
    
    def _build_personality_instructions(
        self,
        personality_config: Dict,
        relationship_state: Optional[Dict]
    ) -> List[str]:
        """Build personality trait and behavior instructions."""
        instructions = []
        
        traits = personality_config.get('traits', {})
        behaviors = personality_config.get('behaviors', {})
        relationship_type = personality_config.get('relationship_type')
        speaking_style = personality_config.get('custom', {}).get('speaking_style')
        
        # Relationship context
        if relationship_type:
            relationship_names = {
                'friend': 'We have a friendship',
                'mentor': 'I am your mentor',
                'coach': 'I am your coach',
                'therapist': 'I am your therapist',
                'partner': 'We are creative partners',
                'advisor': 'I am your advisor',
                'assistant': 'I am your assistant'
            }
            instructions.append(f"📋 Relationship: {relationship_names.get(relationship_type, 'I am your assistant')}")
        
        # Relationship depth (if available)
        if relationship_state:
            messages = relationship_state.get('total_messages', 0)
            days_known = relationship_state.get('days_known', 0)
            depth_score = relationship_state.get('relationship_depth_score', 0)
            
            if messages > 0:
                instructions.append(f"📊 History: {messages} conversations, {days_known} days together (depth: {depth_score:.1f}/10)")
                
                # Adjust tone based on relationship depth
                if depth_score < 2:
                    instructions.append("  💡 We're just getting to know each other. Be welcoming and establish rapport.")
                elif depth_score < 5:
                    instructions.append("  💡 We have a developing relationship. Reference our history naturally.")
                elif depth_score >= 7:
                    instructions.append("  💡 We have a deep connection. You know me well - speak with familiarity and warmth.")
        
        # Speaking style
        if speaking_style:
            instructions.append(f"🗣️ Speaking Style: {speaking_style}")
        
        # Trait-based instructions
        trait_instructions = []
        
        # Humor
        humor = traits.get('humor_level', 5)
        if humor <= 3:
            trait_instructions.append("Be serious and professional. Avoid jokes or humor.")
        elif humor >= 8:
            trait_instructions.append("Use humor frequently! Make jokes, be playful, and keep things light.")
        elif humor >= 6:
            trait_instructions.append("Use occasional humor when appropriate to keep things engaging.")
        
        # Formality
        formality = traits.get('formality_level', 5)
        if formality <= 3:
            trait_instructions.append("Be very casual and relaxed. Use contractions, slang if appropriate, be conversational.")
        elif formality >= 8:
            trait_instructions.append("Maintain high formality. Use proper grammar, avoid contractions, be respectful.")
        elif formality >= 6:
            trait_instructions.append("Be professional but approachable. Balanced formality.")
        
        # Enthusiasm
        enthusiasm = traits.get('enthusiasm_level', 5)
        if enthusiasm <= 3:
            trait_instructions.append("Be calm, measured, and reserved in your responses.")
        elif enthusiasm >= 8:
            trait_instructions.append("Show high energy and excitement! Use exclamation points! Be enthusiastic!")
        elif enthusiasm >= 6:
            trait_instructions.append("Show moderate enthusiasm and positive energy.")
        
        # Empathy
        empathy = traits.get('empathy_level', 7)
        if empathy <= 3:
            trait_instructions.append("Focus on logic and facts. Be objective and analytical.")
        elif empathy >= 8:
            trait_instructions.append("Be highly empathetic. Tune into emotions, validate feelings, show deep understanding.")
        elif empathy >= 6:
            trait_instructions.append("Balance empathy with logic. Be understanding but also practical.")
        
        # Directness
        directness = traits.get('directness_level', 5)
        if directness <= 3:
            trait_instructions.append("Be gentle and tactful. Soften difficult truths, be diplomatic.")
        elif directness >= 8:
            trait_instructions.append("Be very direct and straightforward. Get to the point, be honest and clear.")
        elif directness >= 6:
            trait_instructions.append("Be direct but considerate. Clear communication without being harsh.")
        
        # Curiosity
        curiosity = traits.get('curiosity_level', 5)
        if curiosity <= 3:
            trait_instructions.append("Wait for the user to provide information. Be responsive rather than proactive.")
        elif curiosity >= 8:
            trait_instructions.append("Ask lots of questions! Be very curious and explore topics deeply.")
        elif curiosity >= 6:
            trait_instructions.append("Ask clarifying questions when appropriate to better understand.")
        
        # Supportiveness
        supportiveness = traits.get('supportiveness_level', 7)
        if supportiveness <= 3:
            trait_instructions.append("Challenge and push. Be critical when needed, focus on improvement.")
        elif supportiveness >= 8:
            trait_instructions.append("Be highly supportive and encouraging. Celebrate everything, offer constant encouragement.")
        elif supportiveness >= 6:
            trait_instructions.append("Be supportive and encouraging while also being honest.")
        
        # Playfulness
        playfulness = traits.get('playfulness_level', 5)
        if playfulness <= 3:
            trait_instructions.append("Stay serious and focused. Stick to the task at hand.")
        elif playfulness >= 8:
            trait_instructions.append("Be playful and creative! Use imagination, have fun with conversations.")
        elif playfulness >= 6:
            trait_instructions.append("Add occasional playfulness and creativity to keep things interesting.")
        
        if trait_instructions:
            instructions.append("\n🎨 Personality Traits:")
            instructions.extend([f"  • {inst}" for inst in trait_instructions])
        
        # Behavior-based instructions
        behavior_instructions = []
        
        if behaviors.get('asks_questions') is True:
            behavior_instructions.append("Ask questions to better understand the user")
        elif behaviors.get('asks_questions') is False:
            behavior_instructions.append("Avoid asking questions unless absolutely necessary")
        
        if behaviors.get('uses_examples') is True:
            behavior_instructions.append("Use examples and illustrations to clarify points")
        elif behaviors.get('uses_examples') is False:
            behavior_instructions.append("Explain directly without examples")
        
        if behaviors.get('shares_opinions') is True:
            behavior_instructions.append("Share your opinions and perspectives when relevant")
        elif behaviors.get('shares_opinions') is False:
            behavior_instructions.append("Stay neutral and objective, avoid sharing opinions")
        
        if behaviors.get('challenges_user') is True:
            behavior_instructions.append("Challenge the user to grow and think differently")
        elif behaviors.get('challenges_user') is False:
            behavior_instructions.append("Be supportive without challenging or pushing")
        
        if behaviors.get('celebrates_wins') is True:
            behavior_instructions.append("Celebrate achievements and positive moments")
        elif behaviors.get('celebrates_wins') is False:
            behavior_instructions.append("Acknowledge wins briefly, stay focused on next steps")
        
        if behavior_instructions:
            instructions.append("\n✅ Behavioral Guidelines:")
            instructions.extend([f"  • {inst}" for inst in behavior_instructions])
        
        return instructions
    
    def build_chat_messages(
        self,
        system_prompt: str,
        recent_messages: List[Message],
        current_user_message: Optional[str] = None
    ) -> List[Dict[str, str]]:
        """
        Build the complete message list for chat completion.
        
        Args:
            system_prompt: System prompt to use
            recent_messages: Recent conversation history
            current_user_message: Current user message (if starting new turn)
            
        Returns:
            List of message dictionaries ready for LLM API
        """
        messages = []
        
        # Add system message
        messages.append({
            "role": "system",
            "content": system_prompt
        })
        
        # Add conversation history
        for msg in recent_messages:
            messages.append({
                "role": msg.role,
                "content": msg.content
            })
        
        # Add current user message if provided
        if current_user_message:
            messages.append({
                "role": "user",
                "content": current_user_message
            })
        
        return messages
    
    def _build_goal_instructions(self, goal_context: Dict) -> List[str]:
        """
        Build instructions about user's goals and progress.
        
        Args:
            goal_context: Goal tracking context
            
        Returns:
            List of instruction strings
        """
        instructions = []
        
        # Handle new goals detected
        if goal_context.get('new_goals'):
            new_goals_list = [g['title'] for g in goal_context['new_goals']]
            instructions.append(
                f"🎉 NEW GOAL(S) DETECTED: {', '.join(new_goals_list)}"
            )
            instructions.append(
                "- Acknowledge their new goal(s) and show enthusiasm"
            )
            instructions.append(
                "- Offer to help them plan or break it down into steps"
            )
        
        # Handle completions
        if goal_context.get('completions'):
            completions = ', '.join(goal_context['completions'])
            instructions.append(
                f"🏆 GOAL COMPLETED: {completions}"
            )
            instructions.append(
                "- CELEBRATE this achievement enthusiastically!"
            )
            instructions.append(
                "- Ask how they feel about completing it"
            )
        
        # Handle progress updates
        if goal_context.get('progress_updates'):
            for update in goal_context['progress_updates']:
                if update['sentiment'] == 'positive':
                    instructions.append(
                        f"✅ Positive progress on: {update['goal']}"
                    )
                    instructions.append(
                        "- Encourage them and acknowledge their hard work"
                    )
                elif update['sentiment'] == 'negative':
                    instructions.append(
                        f"⚠️ Struggling with: {update['goal']}"
                    )
                    instructions.append(
                        "- Show empathy and offer support"
                    )
                    instructions.append(
                        "- Help them problem-solve or adjust their approach"
                    )
        
        # Show active goals context
        active_goals = goal_context.get('active_goals', [])
        if active_goals:
            instructions.append("\nUser's Active Goals:")
            for goal in active_goals[:5]:  # Top 5
                progress = goal.get('progress_percentage', 0)
                instructions.append(
                    f"- {goal['title']} ({goal['category']}) - {progress:.0f}% complete"
                )
            
            instructions.append("\nGoal-Aware Guidance:")
            instructions.append(
                "- Be a supportive coach for their goals"
            )
            instructions.append(
                "- Reference their goals naturally when relevant"
            )
            instructions.append(
                "- Ask about progress if they haven't mentioned it recently"
            )
            instructions.append(
                "- Celebrate wins, no matter how small"
            )
            instructions.append(
                "- Help them stay motivated and overcome obstacles"
            )
            
            # Add specific guidance based on goal categories
            categories = set(g['category'] for g in active_goals)
            if 'learning' in categories:
                instructions.append(
                    "- For learning goals: Share tips, encourage practice, track their progress"
                )
            if 'health' in categories:
                instructions.append(
                    "- For health goals: Be supportive, celebrate consistency, encourage rest"
                )
            if 'career' in categories:
                instructions.append(
                    "- For career goals: Offer strategic advice, build confidence, celebrate milestones"
                )
        
        return instructions
    
    def format_memory_for_display(self, memory: Memory) -> str:
        """
        Format a memory for human-readable display.
        
        Args:
            memory: Memory to format
            
        Returns:
            Formatted memory string
        """
        parts = [memory.content]
        
        metadata = []
        if memory.memory_type:
            metadata.append(f"type: {memory.memory_type.value}")
        if memory.importance is not None:
            metadata.append(f"importance: {memory.importance:.2f}")
        if memory.similarity_score is not None:
            metadata.append(f"relevance: {memory.similarity_score:.2f}")
        
        if metadata:
            parts.append(f" [{', '.join(metadata)}]")
        
        return "".join(parts)

