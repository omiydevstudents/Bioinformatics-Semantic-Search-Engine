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
                # Create batch grading prompt
                system_prompt = """You are a bioinformatics expert grading tool relevance.
                
                Assess whether multiple bioinformatics tools are relevant to a user's query.
                For each tool, consider:
                - Tool name and description
                - Tool category and functionality
                - Query intent and domain
                - Semantic similarity
                
                Grade each tool with 'yes' or 'no' and provide brief reasoning.
                Return results in the exact format specified."""

                # Build the batch prompt
                tools_text = ""
                for i, tool in enumerate(tool_batch, 1):
                    tools_text += f"\n{i}. Tool: {tool.get('name', 'Unknown')}\n"
                    tools_text += f"   Category: {tool.get('category', 'Unknown')}\n"
                    tools_text += f"   Description: {tool.get('content', '')[:150]}...\n"

                prompt = ChatPromptTemplate.from_messages([
                    ("system", system_prompt),
                    ("human", f"Query: {query}\n\nTools to grade:{tools_text}\n\n"
                             f"Grade each tool as 'yes' (relevant) or 'no' (not relevant) with brief reasoning.")
                ])

                # Create structured output for batch grading
                class BatchGrade(BaseModel):
                    grades: List[Dict[str, str]] = Field(
                        description="List of grades for each tool in order, each with 'score' (yes/no) and 'reasoning'"
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
                        
                        if grade.get('score') == 'yes':
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
                
                Check if the analysis and recommendations are supported by the provided tools and papers.
                Look for:
                - Claims that match the tool descriptions
                - Recommendations that align with available tools
                - Analysis that references specific tools/papers
                
                Give a binary score 'yes' or 'no' with reasoning."""),
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
                ("system", """You are a bioinformatics expert assessing whether results address the user's query.
                
                Check if the results provide useful information for the query.
                Consider:
                - Relevance of tools to the query
                - Completeness of the response
                - Practical usefulness
                
                Give a binary score 'yes' or 'no' with reasoning."""),
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
            
            print(f"🔍 Quality Grades:")
            print(f"   Grounded: {grounding_grade['binary_score']} - {grounding_grade['reasoning']}")
            print(f"   Addresses Query: {answer_grade['binary_score']} - {answer_grade['reasoning']}")
            
        except Exception as e:
            print(f"⚠️  Error grading recommendations: {e}")
            results['quality_grades'] = {
                'grounded': 'unknown',
                'grounded_reasoning': f"Grading failed: {e}",
                'addresses_query': 'unknown',
                'addresses_reasoning': f"Grading failed: {e}",
                'overall_quality': 'unknown'
            }
        
        return results
    
    async def transform_query(self, query: str, previous_results: Optional[Dict] = None) -> str:
        """
        Transform the query to improve retrieval.
        
        Args:
            query: Original query
            previous_results: Results from previous iteration (if any)
            
        Returns:
            Improved query
        """
        if not self.use_gemini:
            return query
        
        try:
            # Create query transformation prompt
            system_prompt = """You are a bioinformatics expert improving search queries.
            
            Transform the query to be more effective for bioinformatics tool discovery.
            Consider:
            - Adding relevant bioinformatics terminology
            - Including specific tool categories
            - Expanding to related concepts
            - Making the query more specific or broader as needed
            
            If previous results were poor, make the query broader.
            If previous results were too broad, make the query more specific."""
            
            # Add context from previous results if available
            context = ""
            if previous_results:
                tool_count = len(previous_results.get('chroma_tools', []))
                paper_count = len(previous_results.get('papers', []))
                quality = previous_results.get('quality_grades', {}).get('overall_quality', 'unknown')
                context = f"\n\nPrevious Results: {tool_count} tools, {paper_count} papers, quality: {quality}"
            
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
    
    async def discover_tools_self_rag(self, query: str) -> Dict:
        """
        Main Self-RAG enhanced tool discovery method.
        Adds timing/profiling and early stopping for speed.
        """
        import time
        print(f"🤖 Self-RAG Enhanced Tool Discovery")
        print(f"Query: {query}")
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
            results = await self.base_agent.discover_tools_enhanced(current_query)
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