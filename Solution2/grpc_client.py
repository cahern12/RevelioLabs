import grpc
from seniority_model_pb2 import SeniorityRequestBatch, SeniorityRequest
from seniority_model_pb2_grpc import SeniorityModelStub

class GRPCClient:
    def __init__(self, server_address):
        self.channel = grpc.insecure_channel(server_address)
        self.grpc_stub = SeniorityModelStub(self.channel)

    def infer_seniority(self, missing_pairs):
        """Make a batch gRPC call to infer seniority levels for missing pairs."""
        requests = [SeniorityRequest(uuid=data["uuid"], company=data["company"], title=data["title"]) for data in missing_pairs.values()]
        request_batch = SeniorityRequestBatch(batch=requests)
        response_batch = self.grpc_stub.InferSeniority(request_batch)
        inferred_seniorities = {response.uuid: response.seniority for response in response_batch.batch}
        return inferred_seniorities
