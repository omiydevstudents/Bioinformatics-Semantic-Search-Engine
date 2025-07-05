"""
Self-RAG Enhanced ToolDiscoveryAgent

Implements self-reflection and quality control for bioinformatics tool discovery.
Based on LangGraph Self-RAG concepts with bioinformatics-specific adaptations.
"""

import asyncio
import sys
import os
from typing import Dict, List, Optional
from pydantic import BaseModel, Field

# Add src to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.tool_discovery_agent import ToolDiscoveryAgent
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv

load_dotenv()

# Data Models for Self-RAG Grading
class GradeDocuments(BaseModel):
    """Binary score for relevance check on retrieved tools."""
    binary_score: str = Field(
        description="Tools are relevant to the query, 'yes' or 'no'"
    )
    reasoning: str = Field(
        description="Brief explanation for the relevance score"
    )

class GradeHallucinations(BaseModel):
    """Binary score for hallucination detection in recommendations."""
    binary_score: str = Field(
        description="Recommendations are grounded in facts, 'yes' or 'no'"
    )
    reasoning: str = Field(
        description="Brief explanation for the grounding score"
    )

class GradeAnswer(BaseModel):
    """Binary score to assess if results address the query."""
    binary_score: str = Field(
        description="Results address the query, 'yes' or 'no'"
    )
    reasoning: str = Field(
        description="Brief explanation for the answer score"
    )

class QueryTransform(BaseModel):
    """Improved query for better retrieval."""
    improved_query: str = Field(
        description="Enhanced query optimized for bioinformatics tool discovery"
    )
    reasoning: str = Field(
        description="Explanation of how the query was improved"
    )

class SelfRAGAgent:
    """
    Self-RAG enhanced tool discovery agent with intelligent self-reflection.
    
    Features:
    - Automatic query refinement
    - Tool relevance grading
    - Hallucination detection
    - Result quality assessment
    - Iterative improvement
    """
    
    def __init__(self):
        """Initialize the Self-RAG agent with all components."""
        self.base_agent = ToolDiscoveryAgent()
        self.max_iterations = 3
        self.iteration_count = 0
        
        # Initialize Gemini for grading
        google_api_key = os.getenv("GOOGLE_API_KEY")
        if google_api_key:
            self.gemini = ChatGoogleGenerativeAI(
                model="gemini-1.5-pro",
                api_key=google_api_key,
                temperature=0.1,  # Lower temperature for consistent grading
                max_tokens=500
            )
            self.use_gemini = True
        else:
            self.gemini = None
            self.use_gemini = False
            print("⚠️  GOOGLE_API_KEY not found. Self-RAG grading disabled.")
    
    async def grade_tool_relevance(self, query: str, tools: List[Dict]) -> List[Dict]:
        """
        Grade whether retrieved tools are relevant to the query.
        Now uses LLM call batching for maximum speed - processes multiple tools in a single LLM call.
        """
        if not self.use_gemini or not tools:
            return tools

        # Batch size optimization - 3-5 tools per batch is optimal for most LLMs
        BATCH_SIZE = 4
        
        async def grade_batch(tool_batch: List[Dict]) -> List[Dict]:
            """Grade a batch of tools in a single LLM call."""
            try:
                # Create dynamic grading prompt
                grading_prompt = f"""
You are an expert bioinformatics analyst evaluating tool relevance for this query: "{query}"

Your task is to assess whether each tool is relevant to the user's needs.

EVALUATION CRITERIA:
1. **Direct Relevance**: Does the tool directly address the user's query or task?
2. **Functional Match**: Does the tool's functionality align with what the user is looking for?
3. **Domain Appropriateness**: Is the tool suitable for the scientific domain mentioned?
4. **Practical Utility**: Would this tool be useful for the user's specific needs?

GRADING GUIDELINES:
- **RELEVANT**: Tool directly addresses the query or is clearly useful for the task
- **NOT RELEVANT**: Tool is unrelated to the query or inappropriate for the task

IMPORTANT CONSIDERATIONS:
- Consider tool variations and aliases (e.g., "iqtree" = "IQ-TREE", "MACSr" = "MACS2 R version")
- Look for tools that might be relevant even if not an exact match
- Consider complementary tools that could be part of a workflow
- Don't be overly strict - if a tool could be useful, mark it as relevant
- Focus on the user's actual needs, not just exact keyword matches

For each tool, provide:
1. A binary score: 'RELEVANT' or 'NOT RELEVANT'
2. Brief reasoning explaining your decision

Please grade each tool based on its relevance to the query: "{query}"
"""

                # Build the batch prompt
                tools_text = ""
                for i, tool in enumerate(tool_batch, 1):
                    tools_text += f"\n{i}. Tool: {tool.get('name', 'Unknown')}\n"
                    tools_text += f"   Category: {tool.get('category', 'Unknown')}\n"
                    tools_text += f"   Description: {tool.get('content', '')[:150]}...\n"

                prompt = ChatPromptTemplate.from_messages([
                    ("system", grading_prompt),
                    ("human", f"Query: {query}\n\nTools to grade:{tools_text}\n\n"
                             f"Grade each tool as 'RELEVANT' or 'NOT RELEVANT' with brief reasoning.")
                ])

                # Create structured output for batch grading
                class BatchGrade(BaseModel):
                    grades: List[Dict[str, str]] = Field(
                        description="List of grades for each tool in order, each with 'score' (RELEVANT/NOT RELEVANT) and 'reasoning'"
                    )

                # Grade the batch
                if self.gemini is None:
                    raise ValueError("Gemini client not initialized")
                chain = prompt | self.gemini.with_structured_output(BatchGrade)
                batch_result = await chain.ainvoke({
                    "query": query,
                    "tools_count": len(tool_batch)
                })

                # Ensure dict access
                if not isinstance(batch_result, dict):
                    batch_result = batch_result.dict() if hasattr(batch_result, 'dict') else dict(batch_result)

                # Apply grades to tools
                graded_tools = []
                grades = batch_result.get('grades', [])
                
                for i, tool in enumerate(tool_batch):
                    if i < len(grades):
                        grade = grades[i]
                        tool['relevance_grade'] = grade.get('score', 'unknown')
                        tool['relevance_reasoning'] = grade.get('reasoning', 'No reasoning provided')
                        
                        if grade.get('score') == 'RELEVANT':
                            print(f"✅ Tool '{tool.get('name')}' graded as RELEVANT")
                            graded_tools.append(tool)
                        else:
                            print(f"❌ Tool '{tool.get('name')}' graded as NOT RELEVANT: {grade.get('reasoning', '')}")
                    else:
                        # Fallback if LLM didn't return enough grades
                        tool['relevance_grade'] = 'unknown'
                        tool['relevance_reasoning'] = 'Batch grading failed - insufficient results'
                        graded_tools.append(tool)

                return graded_tools

            except Exception as e:
                print(f"⚠️  Error grading batch: {e}")
                # Fallback: mark all tools in batch as unknown
                for tool in tool_batch:
                    tool['relevance_grade'] = 'unknown'
                    tool['relevance_reasoning'] = f"Batch grading failed: {e}"
                return tool_batch

        # Split tools into batches
        batches = [tools[i:i + BATCH_SIZE] for i in range(0, len(tools), BATCH_SIZE)]
        print(f"📦 Processing {len(tools)} tools in {len(batches)} batches of {BATCH_SIZE}")

        # Process all batches in parallel
        batch_results = await asyncio.gather(*(grade_batch(batch) for batch in batches))
        
        # Flatten results
        all_graded_tools = []
        for batch_result in batch_results:
            all_graded_tools.extend(batch_result)

        print(f"🎯 Batch grading complete: {len(all_graded_tools)} tools processed")
        return all_graded_tools
    
    async def grade_recommendations(self, query: str, results: Dict) -> Dict:
        """
        Grade whether the recommendations are grounded and address the query.
        
        Args:
            query: Original search query
            results: Discovery results
            
        Returns:
            Results with quality grades
        """
        if not self.use_gemini:
            return results
        
        try:
            # Prepare context for grading
            context_parts = []
            
            # Add tool information
            chroma_tools = results.get('chroma_tools', [])
            if chroma_tools:
                tool_info = "\n".join([
                    f"- {tool.get('name')}: {tool.get('content', '')[:100]}..."
                    for tool in chroma_tools[:5]
                ])
                context_parts.append(f"Local Tools:\n{tool_info}")
            
            # Add web tools
            web_tools = results.get('web_tools', [])
            if web_tools:
                web_info = "\n".join([
                    f"- {tool.get('name', 'Unknown')}: {tool.get('description', '')[:100]}..."
                    for tool in web_tools[:3]
                ])
                context_parts.append(f"Web Tools:\n{web_info}")
            
            # Add papers
            papers = results.get('papers', [])
            if papers:
                paper_info = "\n".join([
                    f"- {paper.get('title', 'Unknown')}: {paper.get('abstract', '')[:100]}..."
                    for paper in papers[:3]
                ])
                context_parts.append(f"Scientific Papers:\n{paper_info}")
            
            context = "\n\n".join(context_parts)
            analysis = results.get('analysis', '')
            
            # Grade grounding (hallucination detection)
            grounding_prompt = ChatPromptTemplate.from_messages([
                ("system", """You are a bioinformatics expert assessing whether recommendations are grounded in facts.
                
                Your task is to evaluate if the analysis and recommendations are supported by the provided tools and papers.
                
                EVALUATION CRITERIA:
                1. **Tool References**: Does the analysis mention and discuss the actual tools provided?
                2. **Accurate Descriptions**: Are tool capabilities described accurately based on the available information?
                3. **Logical Connections**: Do the recommendations logically follow from the available tools?
                4. **No Fabrication**: Does the analysis avoid claiming tools exist that aren't in the results?
                
                IMPORTANT: 
                - Focus on whether the analysis discusses the ACTUAL tools provided
                - Don't penalize for missing popular tools that aren't in the results
                - A good analysis can work with the tools that are available
                - Look for evidence that the analysis is based on the provided data
                
                Give a binary score 'yes' or 'no' with clear reasoning."""),
                ("human", f"Query: {query}\n\nAvailable Information:\n{context}\n\n"
                         f"Analysis/Recommendations:\n{analysis}")
            ])
            
            if self.gemini is None:
                raise ValueError("Gemini client not initialized")
            grounding_chain = grounding_prompt | self.gemini.with_structured_output(GradeHallucinations)
            grounding_grade = await grounding_chain.ainvoke({
                "query": query,
                "context": context,
                "analysis": analysis
            })
            
            # Ensure dict access
            if not isinstance(grounding_grade, dict):
                grounding_grade = grounding_grade.dict() if hasattr(grounding_grade, 'dict') else dict(grounding_grade)
            
            # Grade answer quality
            answer_prompt = ChatPromptTemplate.from_messages([
                ("system", """You are a bioinformatics expert assessing whether results address the user's query effectively.
                
                EVALUATION CRITERIA:
                1. **Query Relevance**: Do the results directly address what the user is asking for?
                2. **Useful Information**: Do the recommendations provide actionable insights?
                3. **Completeness**: Given the available tools, is the response comprehensive?
                4. **Practical Value**: Would the user find this response helpful for their task?
                
                IMPORTANT: 
                - Assess quality based on what tools are actually available
                - A good response can be achieved with the tools that are present
                - Focus on whether the analysis helps the user understand and use the available tools
                - Consider the complexity and specificity of the original query
                
                Give a binary score 'yes' or 'no' with clear reasoning."""),
                ("human", f"Query: {query}\n\nResults Summary:\n"
                         f"- Tools found: {len(chroma_tools) + len(web_tools)}\n"
                         f"- Papers found: {len(papers)}\n"
                         f"- Analysis: {analysis[:200]}...")
            ])
            
            if self.gemini is None:
                raise ValueError("Gemini client not initialized")
            answer_chain = answer_prompt | self.gemini.with_structured_output(GradeAnswer)
            answer_grade = await answer_chain.ainvoke({
                "query": query,
                "tools_count": len(chroma_tools) + len(web_tools),
                "papers_count": len(papers),
                "analysis": analysis[:200]
            })
            
            # Ensure dict access
            if not isinstance(answer_grade, dict):
                answer_grade = answer_grade.dict() if hasattr(answer_grade, 'dict') else dict(answer_grade)
            
            # Add grades to results
            results['quality_grades'] = {
                'grounded': grounding_grade['binary_score'],
                'grounded_reasoning': grounding_grade['reasoning'],
                'addresses_query': answer_grade['binary_score'],
                'addresses_reasoning': answer_grade['reasoning'],
                'overall_quality': 'good' if (grounding_grade['binary_score'] == 'yes' and 
                                            answer_grade['binary_score'] == 'yes') else 'needs_improvement'
            }
            
            # Generate follow-up suggestions based on results and quality
            follow_up_suggestions = await self.generate_follow_up_suggestions(query, results)
            results['follow_up_suggestions'] = follow_up_suggestions
            
            print(f"🔍 Quality Grades:")
            print(f"   Grounded: {grounding_grade['binary_score']} - {grounding_grade['reasoning']}")
            print(f"   Addresses Query: {answer_grade['binary_score']} - {answer_grade['reasoning']}")
            print(f"💡 Follow-up suggestions: {len(follow_up_suggestions)} generated")
            
        except Exception as e:
            print(f"⚠️  Error grading recommendations: {e}")
            results['quality_grades'] = {
                'grounded': 'unknown',
                'grounded_reasoning': f"Grading failed: {e}",
                'addresses_query': 'unknown',
                'addresses_reasoning': f"Grading failed: {e}",
                'overall_quality': 'unknown'
            }
            results['follow_up_suggestions'] = []
        
        return results
    
    async def generate_follow_up_suggestions(self, query: str, results: Dict) -> List[str]:
        """
        Generate helpful follow-up suggestions based on search results and quality assessment.
        
        Args:
            query: Original search query
            results: Search results and quality grades
            
        Returns:
            List of suggested follow-up questions
        """
        if not self.use_gemini:
            return []
        
        try:
            # Prepare context for suggestions
            quality_grades = results.get('quality_grades', {})
            overall_quality = quality_grades.get('overall_quality', 'unknown')
            grounded = quality_grades.get('grounded', 'unknown')
            addresses_query = quality_grades.get('addresses_query', 'unknown')
            
            # Count available tools
            chroma_tools = results.get('chroma_tools', [])
            web_tools = results.get('web_tools', [])
            papers = results.get('papers', [])
            total_tools = len(chroma_tools) + len(web_tools)
            
            # Create suggestion prompt
            prompt = f"""
You are an expert bioinformatics consultant helping users refine their tool discovery queries.

ORIGINAL QUERY: {query}

SEARCH RESULTS:
- Total tools found: {total_tools}
- Local tools: {len(chroma_tools)}
- Web tools: {len(web_tools)}
- Scientific papers: {len(papers)}
- Overall quality: {overall_quality}
- Grounded in facts: {grounded}
- Addresses query: {addresses_query}

Your task is to suggest 3-5 helpful follow-up questions that would help the user get better results.

SUGGESTION STRATEGIES:
1. **If quality is poor**: Suggest ways to make the query more specific or broader
2. **If few tools found**: Suggest related terms or alternative approaches
3. **If tools found but not ideal**: Suggest refinements based on use cases
4. **If good results**: Suggest complementary tools or next steps
5. **If specific domain**: Suggest related domains or applications

EXAMPLES:
- "I need more specific tools for [specific task]"
- "Can you find tools that work with [specific data type]?"
- "I'm looking for tools that can handle [specific requirement]"
- "Are there any tools for [related workflow step]?"
- "Can you find tools that integrate with [specific platform]?"

IMPORTANT: Keep each suggestion concise (max 80 characters) and complete. Do not truncate or cut off suggestions.

Generate 3-5 specific, actionable follow-up questions that would help improve the search results.
Return each suggestion on a new line, starting with a dash (-).
"""

            if self.gemini is None:
                raise ValueError("Gemini client not initialized")
            
            response = await self.gemini.ainvoke(prompt)
            suggestions_text = response.content.strip()
            
            # Parse suggestions
            suggestions = []
            for line in suggestions_text.split('\n'):
                line = line.strip()
                if line.startswith('-') or line.startswith('•'):
                    suggestion = line[1:].strip()
                    if suggestion:
                        suggestions.append(suggestion)
                elif line and not line.startswith('SUGGESTION') and not line.startswith('EXAMPLES') and not line.startswith('Generate'):
                    # If no bullet points, treat each line as a suggestion
                    if len(line) > 10 and len(line) < 200:  # Reasonable length
                        suggestions.append(line)
            
            # Clean up suggestions and ensure they're complete
            cleaned_suggestions = []
            for suggestion in suggestions[:5]:
                # Remove any trailing incomplete text
                if suggestion.endswith('...') or suggestion.endswith('('):
                    suggestion = suggestion.rstrip('...(').strip()
                # Ensure it's a complete sentence
                if suggestion and len(suggestion) > 15:
                    cleaned_suggestions.append(suggestion)
            
            print(f"💡 Generated suggestions: {cleaned_suggestions}")
            return cleaned_suggestions
            
        except Exception as e:
            print(f"⚠️  Error generating follow-up suggestions: {e}")
            return []
    
    async def transform_query(self, query: str, previous_results: Optional[Dict] = None) -> str:
        """
        Transform the query to improve retrieval using dynamic, flexible approach.
        
        Args:
            query: Original query
            previous_results: Results from previous iteration (if any)
            
        Returns:
            Improved query
        """
        if not self.use_gemini:
            return query
        
        try:
            # Create dynamic query transformation prompt
            system_prompt = """You are an expert at improving search queries for bioinformatics tool discovery.
            
            Your goal is to transform queries to be more effective for finding relevant tools and resources.
            
            TRANSFORMATION STRATEGIES:
            1. **Add Context**: Include relevant scientific terminology and concepts
            2. **Expand Scope**: Add related terms that might help find more tools
            3. **Be Specific**: Make vague queries more specific when possible
            4. **Include Categories**: Add tool categories or types that might be relevant
            5. **Alternative Phrasings**: Include different ways to describe the same concept
            
            ADAPTIVE APPROACH:
            - If previous results were poor: Make the query broader and more inclusive
            - If previous results were too broad: Make the query more specific and focused
            - If previous results were good but incomplete: Add complementary terms
            - Consider the complexity and specificity of the original query
            
            GUIDELINES:
            - Don't change the core intent of the query
            - Add relevant terms without making it too long
            - Focus on terms that would help find bioinformatics tools
            - Consider both the scientific domain and the technical requirements
            - Adapt to the user's level of expertise (don't over-complicate simple queries)
            
            Return an improved query that maintains the original intent while being more effective for tool discovery."""
            
            # Add context from previous results if available
            context = ""
            if previous_results:
                tool_count = len(previous_results.get('chroma_tools', []))
                paper_count = len(previous_results.get('papers', []))
                quality = previous_results.get('quality_grades', {}).get('overall_quality', 'unknown')
                context = f"\n\nPrevious Results: {tool_count} tools, {paper_count} papers, quality: {quality}"
                
                # Add specific feedback based on previous results
                if tool_count == 0:
                    context += "\nNo tools found - query may be too specific or use uncommon terms"
                elif quality == 'needs_improvement':
                    context += "\nResults need improvement - query may need refinement"
            
            prompt = ChatPromptTemplate.from_messages([
                ("system", system_prompt),
                ("human", f"Original Query: {query}{context}\n\n"
                         f"Please provide an improved query for bioinformatics tool discovery.")
            ])
            
            if self.gemini is None:
                raise ValueError("Gemini client not initialized")
            chain = prompt | self.gemini.with_structured_output(QueryTransform)
            transform_result = await chain.ainvoke({
                "query": query,
                "previous_results": context
            })

            # Ensure dict access for LLM output
            if not isinstance(transform_result, dict):
                transform_result = transform_result.dict() if hasattr(transform_result, 'dict') else dict(transform_result)

            improved_query = transform_result['improved_query']
            print(f"🔄 Query Transformation:")
            print(f"   Original: {query}")
            print(f"   Improved: {improved_query}")
            print(f"   Reasoning: {transform_result['reasoning']}")
            
            return improved_query
            
        except Exception as e:
            print(f"⚠️  Error transforming query: {e}")
            return query
    
    async def decide_next_action(self, results: Dict, iteration: int) -> str:
        """
        Decide the next action based on current results and iteration count.
        
        Args:
            results: Current discovery results
            iteration: Current iteration number
            
        Returns:
            Next action: 'accept', 'refine_query', or 'retrieve_more'
        """
        if iteration >= self.max_iterations:
            return 'accept'
        
        quality_grades = results.get('quality_grades', {})
        overall_quality = quality_grades.get('overall_quality', 'unknown')
        
        # Check if we have good results
        if overall_quality == 'good':
            return 'accept'
        
        # Check if we have any results
        total_results = results.get('total_results', 0)
        if total_results == 0:
            return 'refine_query'
        
        # Check quality indicators
        grounded = quality_grades.get('grounded', 'unknown')
        addresses_query = quality_grades.get('addresses_query', 'unknown')
        
        if grounded == 'no' or addresses_query == 'no':
            return 'refine_query'
        
        # If we have some results but could be better, try to retrieve more
        if total_results < 5:
            return 'retrieve_more'
        
        return 'accept'
    
    async def discover_tools_self_rag(self, query: str, max_results: int = 10) -> Dict:
        """
        Main Self-RAG enhanced tool discovery method.
        Adds timing/profiling and early stopping for speed.
        """
        import time
        print(f"🤖 Self-RAG Enhanced Tool Discovery")
        print(f"Query: {query}")
        print(f"Max results per section: {max_results}")
        print("=" * 60)

        original_query = query
        current_query = query
        iteration_history = []
        best_results = None
        start_time = time.time()

        for iteration in range(self.max_iterations):
            print(f"\n🔄 Iteration {iteration + 1}/{self.max_iterations}")
            print("-" * 40)
            t0 = time.time()

            # Discover tools with current query
            t1 = time.time()
            results = await self.base_agent.discover_tools_enhanced(current_query, max_results)
            print(f"⏱️ Tool discovery: {time.time() - t1:.2f}s")

            # Grade tool relevance
            t2 = time.time()
            if results.get('chroma_tools'):
                results['chroma_tools'] = await self.grade_tool_relevance(
                    current_query, results['chroma_tools']
                )
            print(f"⏱️ Tool grading: {time.time() - t2:.2f}s")

            # Grade overall recommendations
            t3 = time.time()
            results = await self.grade_recommendations(current_query, results)
            print(f"⏱️ Recommendation grading: {time.time() - t3:.2f}s")

            # Add iteration info
            results['iteration'] = iteration + 1
            results['query_used'] = current_query

            # Store in history
            iteration_history.append(results)

            # Update best results if this is better
            if not best_results or (
                results.get('quality_grades', {}).get('overall_quality') == 'good' and
                best_results.get('quality_grades', {}).get('overall_quality') != 'good'
            ):
                best_results = results

            # Decide next action
            next_action = await self.decide_next_action(results, iteration)

            print(f"\n🎯 Decision: {next_action.upper()}")

            # Early stopping: stop if quality is good or time budget exceeded
            if next_action == 'accept' or (time.time() - start_time > 30):
                print("✅ Accepting current results (early stop if needed)")
                break
            elif next_action == 'refine_query':
                print("🔄 Refining query for better results")
                current_query = await self.transform_query(original_query, results)
            elif next_action == 'retrieve_more':
                print("🔍 Attempting to retrieve more results")
                break

            print(f"⏱️ Iteration total: {time.time() - t0:.2f}s")

        # Prepare final results
        final_results = best_results or results
        final_results['original_query'] = original_query
        final_results['iteration_history'] = iteration_history
        final_results['total_iterations'] = len(iteration_history)
        final_results['self_rag_enhanced'] = True

        print(f"\n🎉 Self-RAG Discovery Complete!")
        print(f"Total iterations: {len(iteration_history)}")
        print(f"Final quality: {final_results.get('quality_grades', {}).get('overall_quality', 'unknown')}")
        print(f"⏱️ Total Self-RAG time: {time.time() - start_time:.2f}s")

        return final_results
    
    async def close(self):
        """Clean up resources."""
        await self.base_agent.close()


# Example usage and testing
async def test_self_rag_agent():
    """Test the Self-RAG enhanced agent."""
    agent = SelfRAGAgent()
    
    test_queries = [
        "machine learning for biology",
        "sequence alignment tools",
        "protein structure prediction"
    ]
    
    for query in test_queries:
        print(f"\n🧪 Testing Self-RAG with: '{query}'")
        print("=" * 60)
        
        try:
            results = await agent.discover_tools_self_rag(query)
            
            print(f"\n📊 Final Results Summary:")
            print(f"   Original query: {results['original_query']}")
            print(f"   Final query: {results['query_used']}")
            print(f"   Iterations: {results['total_iterations']}")
            print(f"   Total results: {results['total_results']}")
            print(f"   Quality: {results.get('quality_grades', {}).get('overall_quality', 'unknown')}")
            
            # Show graded tools
            chroma_tools = results.get('chroma_tools', [])
            if chroma_tools:
                print(f"\n🔍 Graded ChromaDB Tools:")
                for i, tool in enumerate(chroma_tools[:3], 1):
                    grade = tool.get('relevance_grade', 'unknown')
                    print(f"   {i}. {tool['name']} - Grade: {grade}")
            
        except Exception as e:
            print(f"❌ Error: {e}")
    
    await agent.close()
    print("\n✅ Self-RAG testing completed!")


if __name__ == "__main__":
    asyncio.run(test_self_rag_agent()) 