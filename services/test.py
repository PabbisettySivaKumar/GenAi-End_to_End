from langfuse import Langfuse
import os
from dotenv import load_dotenv

load_dotenv()

lf = Langfuse(
    public_key=os.getenv("LANGFUSE_PUBLIC_KEY") or "pk_yourkey",
    secret_key=os.getenv("LANGFUSE_SECRET_KEY") or "sk_yourkey",
    host=os.getenv("LANGFUSE_HOST", "http://localhost:3000")
)

# 1️⃣  Create a top-level trace
trace = lf.create_trace(name="api_test_trace", input="Testing Langfuse v3.8.1")

# 2️⃣  Create a child span (e.g. retrieval)
span = lf.create_span(
    trace_id=trace.id,
    name="retrieval_step",
    input="Running retrieval step"
)
span.end(output="✅ Retrieved successfully")

# 3️⃣  Create a generation span
gen = lf.create_generation(
    trace_id=trace.id,
    name="ollama_generation_test",
    model="llama3.1",
    input="What is Langfuse?"
)
gen.end(output="✅ Langfuse working locally!")

# 4️⃣  Close the trace and flush
trace.end(output="✅ All steps completed successfully")
lf.flush()

print("✅ Trace logged successfully — check your Langfuse dashboard.")
