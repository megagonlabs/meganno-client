from sentence_transformers import SentenceTransformer

model = SentenceTransformer('all-MiniLM-L6-v2')
# set metadata generation function for service object demo
demo.set_metadata("bert-embedding",
                  lambda x: list(model.encode(x).astype(float)), 500)