from __future__ import annotations

import hashlib
from pathlib import Path
from types import SimpleNamespace

from synaptic_tuner.api.v1 import RunRef,VerifiedArtifactDescriptor
from tuner.project.context import ProjectContext
from synaptic_host.artifacts import (
    ArtifactDestinationsV1,HostArtifactPublisherV1,
    HuggingFaceDestinationV1,LocalDestinationV1,
)


class Repository:
    def __init__(self):self.values={}
    def load_artifact_publication(self,p,r,d):return self.values.get((p,r,d))
    def commit_artifact_publication(self,p,r,fp,d,raw):
        prior=self.values.setdefault((p,r,d),raw)
        if prior!=raw:raise ValueError("collision")
        return prior


class Source:
    def __init__(self):
        self.run=RunRef("run-1","project-1");self.plan_fingerprint="a"*64;self.reads=[]
        self.values={kind:kind.encode() for kind in ("final_model","tokenizer","training_lineage","training_metrics","workload_record")}
        self.artifacts=tuple(VerifiedArtifactDescriptor(k,hashlib.sha256(v).hexdigest(),len(v)) for k,v in self.values.items())
    def iter_bytes(self,kind,*,maximum):
        self.reads.append(kind)
        value=self.values[kind]
        yield value[:1]
        yield value[1:]


def context(tmp_path):
    project=tmp_path/"project";engine=project/"engine";engine.mkdir(parents=True)
    return ProjectContext.host(engine_root=engine,project_root=project,config_root=project/"training")


def test_local_destination_can_be_an_arbitrary_absolute_host_path(tmp_path):
    source=Source();repository=Repository();external=tmp_path/"external-artifacts"
    publisher=HostArtifactPublisherV1(context=context(tmp_path),repository=repository,destinations=ArtifactDestinationsV1({"external":LocalDestinationV1(str(external))}))
    receipt=publisher.publish(source,"external")
    final=external/"project-1"/"run-1"
    assert final.is_dir() and len(receipt.artifacts)==5 and len(source.reads)==5
    assert publisher.publish(source,"external")==receipt and len(source.reads)==5


def test_huggingface_destination_uses_one_atomic_commit_and_pins_receipt_to_oid(tmp_path):
    calls=[]
    class API:
        def create_commit(self,**kwargs):calls.append(kwargs);return SimpleNamespace(oid="commit123")
    source=Source();publisher=HostArtifactPublisherV1(
        context=context(tmp_path),repository=Repository(),
        destinations=ArtifactDestinationsV1({"hf":HuggingFaceDestinationV1("org/repo","model","main","runs")}),
        hf_token=lambda:"token",hf_api_factory=lambda token:API(),
        hf_operation_factory=lambda path,content:(path,content),
    )
    receipt=publisher.publish(source,"hf")
    assert len(calls)==1 and len(calls[0]["operations"])==5
    assert all("@commit123/" in item.uri for item in receipt.artifacts)


def test_destination_config_contains_no_credentials_and_rejects_extra_fields(tmp_path):
    ctx=context(tmp_path);ctx.config_root.mkdir();(ctx.config_root/"artifacts.json").write_text('{"schema_version":"synaptic-artifact-destinations/v1","destinations":{"local":{"kind":"local","root":"project://.synaptic/artifacts"}}}')
    assert isinstance(ArtifactDestinationsV1.load(ctx).resolve("local"),LocalDestinationV1)
    (ctx.config_root/"artifacts.json").write_text('{"schema_version":"synaptic-artifact-destinations/v1","destinations":{"hf":{"kind":"huggingface","repo_id":"org/repo","repo_type":"model","revision":"main","path_prefix":"runs","token":"forbidden"}}}')
    try:ArtifactDestinationsV1.load(ctx)
    except ValueError:pass
    else:raise AssertionError("literal credential field was accepted")
