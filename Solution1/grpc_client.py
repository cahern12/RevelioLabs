import grpc
from seniority_model_pb2 import SeniorityRequestBatch, SeniorityRequest
from seniority_model_pb2_grpc import SeniorityModelStub

class GRPCClient:
    def __init__(self, server_address):
        self.channel = grpc.insecure_channel(server_address)
        self.grpc_stub = SeniorityModelStub(self.channel)

    def infer_seniority_batch(self, requests):
        """Make a batch gRPC call to infer seniority levels."""
        request_batch = SeniorityRequestBatch(
            batch=[SeniorityRequest(uuid=req["uuid"], company=req["company"], title=req["title"]) for req in requests]
        )
        response_batch = self.grpc_stub.InferSeniority(request_batch)
        return {response.uuid: response.seniority for response in response_batch.batch}
