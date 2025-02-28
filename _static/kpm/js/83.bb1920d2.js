"use strict";(self.webpackChunkpipeline_manager=self.webpackChunkpipeline_manager||[]).push([[83],{19173:(t,e,s)=>{s.d(e,{E:()=>r,e:()=>o});var n=s(57632),i=s(55873);class o{constructor(t,e){if(this.destructed=!1,this.events={destruct:new i.E(this)},!t||!e)throw new Error("Cannot initialize connection with null/undefined for 'from' or 'to' values");this.id=(0,n.Z)(),this.from=t,this.to=e,this.from.connectionCount++,this.to.connectionCount++}destruct(){this.events.destruct.emit(),this.from.connectionCount--,this.to.connectionCount--,this.destructed=!0}}class r{constructor(t,e){if(!t||!e)throw new Error("Cannot initialize connection with null/undefined for 'from' or 'to' values");this.id=(0,n.Z)(),this.from=t,this.to=e}}},45521:(t,e,s)=>{s.d(e,{h:()=>i});var n=s(73933);function i(t){return class extends n.N{constructor(){var e,s;super(),this.type=t.type,this.title=null!==(e=t.title)&&void 0!==e?e:t.type,this.inputs={},this.outputs={},this.calculate=t.calculate?(e,s)=>t.calculate.call(this,e,s):void 0,this.executeFactory("input",t.inputs),this.executeFactory("output",t.outputs),null===(s=t.onCreate)||void 0===s||s.call(this)}onPlaced(){var e;null===(e=t.onPlaced)||void 0===e||e.call(this)}onDestroy(){var e;null===(e=t.onDestroy)||void 0===e||e.call(this)}executeFactory(t,e){Object.keys(e||{}).forEach((s=>{const n=e[s]();"input"===t?this.addInput(s,n):this.addOutput(s,n)}))}}}},70828:(t,e,s)=>{s.d(e,{M:()=>d});var n=s(55873),i=s(12020),o=s(37886),r=s(44653),h=s(44773),a=s(88518);class d{constructor(){this.events={loaded:new n.E(this),beforeRegisterNodeType:new n.w(this),registerNodeType:new n.E(this),beforeUnregisterNodeType:new n.w(this),unregisterNodeType:new n.E(this),beforeAddGraphTemplate:new n.w(this),addGraphTemplate:new n.E(this),beforeRemoveGraphTemplate:new n.w(this),removeGraphTemplate:new n.E(this),registerGraph:new n.E(this),unregisterGraph:new n.E(this)},this.hooks={save:new i.p$(this),load:new i.p$(this)},this.graphTemplateEvents=(0,o.D)(),this.graphTemplateHooks=(0,o.D)(),this.graphEvents=(0,o.D)(),this.graphHooks=(0,o.D)(),this.nodeEvents=(0,o.D)(),this.nodeHooks=(0,o.D)(),this.connectionEvents=(0,o.D)(),this._graphs=new Set,this._nodeTypes=new Map,this._graph=new r.k(this),this._graphTemplates=[],this._loading=!1}get nodeTypes(){return this._nodeTypes}get graph(){return this._graph}get graphTemplates(){return this._graphTemplates}get graphs(){return this._graphs}get loading(){return this._loading}registerNodeType(t,e){var s,n;if(this.events.beforeRegisterNodeType.emit({type:t,options:e}).prevented)return;const i=new t;this._nodeTypes.set(i.type,{type:t,category:null!==(s=null==e?void 0:e.category)&&void 0!==s?s:"default",title:null!==(n=null==e?void 0:e.title)&&void 0!==n?n:i.title}),this.events.registerNodeType.emit({type:t,options:e})}unregisterNodeType(t){const e="string"==typeof t?t:(new t).type;if(this.nodeTypes.has(e)){if(this.events.beforeUnregisterNodeType.emit(e).prevented)return;this._nodeTypes.delete(e),this.events.unregisterNodeType.emit(e)}}addGraphTemplate(t){if(this.events.beforeAddGraphTemplate.emit(t).prevented)return;this._graphTemplates.push(t),this.graphTemplateEvents.addTarget(t.events),this.graphTemplateHooks.addTarget(t.hooks);const e=(0,h.Xk)(t);this.registerNodeType(e,{category:"Subgraphs",title:t.name}),this.events.addGraphTemplate.emit(t)}removeGraphTemplate(t){if(this.graphTemplates.includes(t)){if(this.events.beforeRemoveGraphTemplate.emit(t).prevented)return;const e=(0,h.Ds)(t);for(const t of[this.graph,...this.graphs.values()]){const s=t.nodes.filter((t=>t.type===e));for(const e of s)t.removeNode(e)}this.unregisterNodeType(e),this._graphTemplates.splice(this._graphTemplates.indexOf(t),1),this.graphTemplateEvents.removeTarget(t.events),this.graphTemplateHooks.removeTarget(t.hooks),this.events.removeGraphTemplate.emit(t)}}registerGraph(t){this.graphEvents.addTarget(t.events),this.graphHooks.addTarget(t.hooks),this.nodeEvents.addTarget(t.nodeEvents),this.nodeHooks.addTarget(t.nodeHooks),this.connectionEvents.addTarget(t.connectionEvents),this.events.registerGraph.emit(t),this._graphs.add(t)}unregisterGraph(t){this.graphEvents.removeTarget(t.events),this.graphHooks.removeTarget(t.hooks),this.nodeEvents.removeTarget(t.nodeEvents),this.nodeHooks.removeTarget(t.nodeHooks),this.connectionEvents.removeTarget(t.connectionEvents),this.events.unregisterGraph.emit(t),this._graphs.delete(t)}load(t){try{this._loading=!0,(t=this.hooks.load.execute(t)).graphTemplates.forEach((t=>{const e=new a.o(t,this);this.addGraphTemplate(e)}));const e=this._graph.load(t.graph);return this.events.loaded.emit(),e.forEach((t=>console.warn(t))),e}finally{this._loading=!1}}save(){const t={graph:this.graph.save(),graphTemplates:this.graphTemplates.map((t=>t.save()))};return this.hooks.save.execute(t)}}},44653:(t,e,s)=>{s.d(e,{k:()=>a});var n=s(57632),i=s(55873),o=s(12020),r=s(37886),h=s(19173);class a{get nodes(){return this._nodes}get connections(){return this._connections}get loading(){return this._loading}get destroying(){return this._destroying}constructor(t,e){this.id=(0,n.Z)(),this.inputs=[],this.outputs=[],this.activeTransactions=0,this._nodes=[],this._connections=[],this._loading=!1,this._destroying=!1,this.events={beforeAddNode:new i.w(this),addNode:new i.E(this),beforeRemoveNode:new i.w(this),removeNode:new i.E(this),beforeAddConnection:new i.w(this),addConnection:new i.E(this),checkConnection:new i.w(this),beforeRemoveConnection:new i.w(this),removeConnection:new i.E(this)},this.hooks={save:new o.p$(this),load:new o.p$(this),checkConnection:new o.FQ(this)},this.nodeEvents=(0,r.D)(),this.nodeHooks=(0,r.D)(),this.connectionEvents=(0,r.D)(),this.editor=t,this.template=e,t.registerGraph(this)}addNode(t){if(!this.events.beforeAddNode.emit(t).prevented)return this.nodeEvents.addTarget(t.events),this.nodeHooks.addTarget(t.hooks),t.registerGraph(this),this._nodes.push(t),(t=this.nodes.find((e=>e.id===t.id))).onPlaced(),this.events.addNode.emit(t),t}removeNode(t){if(this.nodes.includes(t)){if(this.events.beforeRemoveNode.emit(t).prevented)return;const e=[...Object.values(t.inputs),...Object.values(t.outputs)];this.connections.filter((t=>e.includes(t.from)||e.includes(t.to))).forEach((t=>this.removeConnection(t))),this._nodes.splice(this.nodes.indexOf(t),1),this.events.removeNode.emit(t),t.onDestroy(),this.nodeEvents.removeTarget(t.events),this.nodeHooks.removeTarget(t.hooks)}}addConnection(t,e){const s=this.checkConnection(t,e);if(!s.connectionAllowed)return;if(this.events.beforeAddConnection.emit({from:t,to:e}).prevented)return;for(const t of s.connectionsInDanger){const e=this.connections.find((e=>e.id===t.id));e&&this.removeConnection(e)}const n=new h.e(s.dummyConnection.from,s.dummyConnection.to);return this.internalAddConnection(n),n}removeConnection(t){if(this.connections.includes(t)){if(this.events.beforeRemoveConnection.emit(t).prevented)return;t.destruct(),this._connections.splice(this.connections.indexOf(t),1),this.events.removeConnection.emit(t),this.connectionEvents.removeTarget(t.events)}}checkConnection(t,e){if(!t||!e)return{connectionAllowed:!1};const s=this.findNodeById(t.nodeId),n=this.findNodeById(e.nodeId);if(s&&n&&s===n)return{connectionAllowed:!1};if(t.isInput&&!e.isInput){const s=t;t=e,e=s}if(t.isInput||!e.isInput)return{connectionAllowed:!1};if(this.connections.some((s=>s.from===t&&s.to===e)))return{connectionAllowed:!1};if(this.events.checkConnection.emit({from:t,to:e}).prevented)return{connectionAllowed:!1};const i=this.hooks.checkConnection.execute({from:t,to:e});if(i.some((t=>!t.connectionAllowed)))return{connectionAllowed:!1};const o=Array.from(new Set(i.flatMap((t=>t.connectionsInDanger))));return{connectionAllowed:!0,dummyConnection:new h.E(t,e),connectionsInDanger:o}}findNodeInterface(t){for(const e of this.nodes){for(const s in e.inputs){const n=e.inputs[s];if(n.id===t)return n}for(const s in e.outputs){const n=e.outputs[s];if(n.id===t)return n}}}findNodeById(t){return this.nodes.find((e=>e.id===t))}load(t){try{this._loading=!0;const e=[];for(let t=this.connections.length-1;t>=0;t--)this.removeConnection(this.connections[t]);for(let t=this.nodes.length-1;t>=0;t--)this.removeNode(this.nodes[t]);this.id=t.id,this.inputs=t.inputs,this.outputs=t.outputs;for(const s of t.nodes){const t=this.editor.nodeTypes.get(s.type);if(!t){e.push(`Node type ${s.type} is not registered`);continue}const n=new t.type;this.addNode(n),n.load(s)}for(const s of t.connections){const t=this.findNodeInterface(s.from),n=this.findNodeInterface(s.to);if(t)if(n){const e=new h.e(t,n);e.id=s.id,this.internalAddConnection(e)}else e.push(`Could not find interface with id ${s.to}`);else e.push(`Could not find interface with id ${s.from}`)}return this.hooks.load.execute(t),e}finally{this._loading=!1}}save(){const t={id:this.id,nodes:this.nodes.map((t=>t.save())),connections:this.connections.map((t=>({id:t.id,from:t.from.id,to:t.to.id}))),inputs:this.inputs,outputs:this.outputs};return this.hooks.save.execute(t)}destroy(){this._destroying=!0;for(const t of this.nodes)this.removeNode(t);this.editor.unregisterGraph(this)}internalAddConnection(t){this.connectionEvents.addTarget(t.events),this._connections.push(t),this.events.addConnection.emit(t)}}},44773:(t,e,s)=>{s.d(e,{Ds:()=>r,Xk:()=>h,qM:()=>o});var n=s(73933),i=s(88272);const o="__baklava_GraphNode-";function r(t){return o+t.id}function h(t){return class extends n.l{constructor(){super(...arguments),this.type=r(t),this._title="GraphNode",this.inputs={},this.outputs={},this.template=t,this.calculate=async(t,e)=>{if(!this.subgraph)throw new Error(`GraphNode ${this.id}: calculate called without subgraph being initialized`);if("object"==typeof e.engine&&e.engine&&"function"==typeof e.engine.runGraph){const s=new Map;for(const t of this.subgraph.nodes)Object.values(t.inputs).forEach((t=>{0===t.connectionCount&&s.set(t.id,t.value)}));Object.entries(t).forEach((([t,e])=>{const n=this.subgraph.inputs.find((e=>e.id===t));s.set(n.nodeInterfaceId,e)}));const n=await e.engine.runGraph(this.subgraph,s,e.globalValues),i=new Map;n.forEach(((t,e)=>{const s=this.subgraph.nodes.find((t=>t.id===e));t.forEach(((t,e)=>{i.set(s.outputs[e].id,t)}))}));const o={};return this.subgraph.outputs.forEach((t=>{o[t.id]=i.get(t.nodeInterfaceId)})),o._calculationResults=n,o}}}get title(){return this._title}set title(t){this.template.name=t}load(t){if(!this.subgraph)throw new Error("Cannot load a graph node without a graph");if(!this.template)throw new Error("Unable to load graph node without graph template");this.subgraph.load(t.graphState),super.load(t)}save(){if(!this.subgraph)throw new Error("Cannot save a graph node without a graph");return{...super.save(),graphState:this.subgraph.save()}}onPlaced(){this.template.events.updated.subscribe(this,(()=>this.initialize())),this.template.events.nameChanged.subscribe(this,(t=>{this._title=t})),this.initialize()}onDestroy(){var t;this.template.events.updated.unsubscribe(this),this.template.events.nameChanged.unsubscribe(this),null===(t=this.subgraph)||void 0===t||t.destroy()}initialize(){this.subgraph&&this.subgraph.destroy(),this.subgraph=this.template.createGraph(),this._title=this.template.name,this.updateInterfaces(),this.events.update.emit(null)}updateInterfaces(){if(!this.subgraph)throw new Error("Trying to update interfaces without graph instance");for(const t of this.subgraph.inputs)t.id in this.inputs?this.inputs[t.id].name=t.name:this.addInput(t.id,new i.I(t.name,void 0));for(const t of Object.keys(this.inputs))this.subgraph.inputs.some((e=>e.id===t))||this.removeInput(t);for(const t of this.subgraph.outputs)t.id in this.outputs?this.outputs[t.id].name=t.name:this.addOutput(t.id,new i.I(t.name,void 0));for(const t of Object.keys(this.outputs))this.subgraph.outputs.some((e=>e.id===t))||this.removeOutput(t);this.addOutput("_calculationResults",new i.I("_calculationResults",void 0).setHidden(!0))}}}},88518:(t,e,s)=>{s.d(e,{o:()=>d});var n=s(57632),i=s(55873),o=s(12020),r=s(44653),h=s(81653),a=s(44773);class d{static fromGraph(t,e){return new d(t.save(),e)}get name(){return this._name}set name(t){this._name=t,this.events.nameChanged.emit(t);const e=this.editor.nodeTypes.get((0,a.Ds)(this));e&&(e.title=t)}constructor(t,e){this.id=(0,n.Z)(),this._name="Subgraph",this.events={nameChanged:new i.E(this),updated:new i.E(this)},this.hooks={beforeLoad:new o.p$(this),afterSave:new o.p$(this)},this.editor=e,t.id&&(this.id=t.id),t.name&&(this._name=t.name),this.update(t)}update(t){this.nodes=t.nodes,this.connections=t.connections,this.inputs=t.inputs,this.outputs=t.outputs,this.events.updated.emit()}save(){return{id:this.id,name:this.name,nodes:this.nodes,connections:this.connections,inputs:this.inputs,outputs:this.outputs}}createGraph(t){const e=new Map,s=t=>{const s=(0,n.Z)();return e.set(t,s),s},i=t=>{const s=e.get(t);if(!s)throw new Error(`Unable to create graph from template: Could not map old id ${t} to new id`);return s},o=t=>(0,h.Q)(t,(t=>({id:s(t.id),templateId:t.id,value:t.value}))),a=this.nodes.map((t=>({...t,id:s(t.id),inputs:o(t.inputs),outputs:o(t.outputs)}))),d=this.connections.map((t=>({id:s(t.id),from:i(t.from),to:i(t.to)}))),u=this.inputs.map((t=>({id:t.id,name:t.name,nodeInterfaceId:i(t.nodeInterfaceId)}))),p=this.outputs.map((t=>({id:t.id,name:t.name,nodeInterfaceId:i(t.nodeInterfaceId)}))),c={id:(0,n.Z)(),nodes:a,connections:d,inputs:u,outputs:p};return t||(t=new r.k(this.editor)),t.load(c),t.template=this,t}}},73933:(t,e,s)=>{s.d(e,{N:()=>a,l:()=>h});var n=s(57632),i=s(55873),o=s(12020),r=s(81653);class h{constructor(){this.id=(0,n.Z)(),this.events={loaded:new i.E(this),beforeAddInput:new i.w(this),addInput:new i.E(this),beforeRemoveInput:new i.w(this),removeInput:new i.E(this),beforeAddOutput:new i.w(this),addOutput:new i.E(this),beforeRemoveOutput:new i.w(this),removeOutput:new i.E(this),update:new i.E(this)},this.hooks={beforeLoad:new o.p$(this),afterSave:new o.p$(this)}}get graph(){return this.graphInstance}addInput(t,e){return this.addInterface("input",t,e)}addOutput(t,e){return this.addInterface("output",t,e)}removeInput(t){return this.removeInterface("input",t)}removeOutput(t){return this.removeInterface("output",t)}registerGraph(t){this.graphInstance=t}load(t){this.hooks.beforeLoad.execute(t),this.id=t.id,this.title=t.title,Object.entries(t.inputs).forEach((([t,e])=>{this.inputs[t]&&(this.inputs[t].load(e),this.inputs[t].nodeId=this.id)})),Object.entries(t.outputs).forEach((([t,e])=>{this.outputs[t]&&(this.outputs[t].load(e),this.outputs[t].nodeId=this.id)})),this.events.loaded.emit(this)}save(){const t=(0,r.Q)(this.inputs,(t=>t.save())),e=(0,r.Q)(this.outputs,(t=>t.save())),s={type:this.type,id:this.id,title:this.title,inputs:t,outputs:e};return this.hooks.afterSave.execute(s)}onPlaced(){}onDestroy(){}initializeIo(){Object.entries(this.inputs).forEach((([t,e])=>this.initializeIntf("input",t,e))),Object.entries(this.outputs).forEach((([t,e])=>this.initializeIntf("output",t,e)))}initializeIntf(t,e,s){s.isInput="input"===t,s.nodeId=this.id,s.events.setValue.subscribe(this,(()=>this.events.update.emit({type:t,name:e,intf:s})))}addInterface(t,e,s){const n="input"===t?this.events.beforeAddInput:this.events.beforeAddOutput,i="input"===t?this.events.addInput:this.events.addOutput,o="input"===t?this.inputs:this.outputs;return!n.emit(s).prevented&&(o[e]=s,this.initializeIntf(t,e,s),i.emit(s),!0)}removeInterface(t,e){const s="input"===t?this.events.beforeRemoveInput:this.events.beforeRemoveOutput,n="input"===t?this.events.removeInput:this.events.removeOutput,i="input"===t?this.inputs[e]:this.outputs[e];if(!i||s.emit(i).prevented)return!1;if(i.connectionCount>0){if(!this.graphInstance)throw new Error("Interface is connected, but no graph instance is specified. Unable to delete interface");this.graphInstance.connections.filter((t=>t.from===i||t.to===i)).forEach((t=>{this.graphInstance.removeConnection(t)}))}return i.events.setValue.unsubscribe(this),"input"===t?delete this.inputs[e]:delete this.outputs[e],n.emit(i),!0}}class a extends h{load(t){super.load(t)}save(){return super.save()}}},88272:(t,e,s)=>{s.d(e,{I:()=>r});var n=s(57632),i=s(55873),o=s(12020);class r{set connectionCount(t){this._connectionCount=t,this.events.setConnectionCount.emit(t)}get connectionCount(){return this._connectionCount}set value(t){this.events.beforeSetValue.emit(t).prevented||(this._value=t,this.events.setValue.emit(t))}get value(){return this._value}constructor(t,e){this.id=(0,n.Z)(),this.nodeId="",this.port=!0,this.hidden=!1,this.events={setConnectionCount:new i.E(this),beforeSetValue:new i.w(this),setValue:new i.E(this),updated:new i.E(this)},this.hooks={load:new o.p$(this),save:new o.p$(this)},this._connectionCount=0,this.name=t,this._value=e}load(t){this.id=t.id,this.templateId=t.templateId,this.value=t.value,this.hooks.load.execute(t)}save(){const t={id:this.id,templateId:this.templateId,value:this.value};return this.hooks.save.execute(t)}setComponent(t){return this.component=t,this}setPort(t){return this.port=t,this}setHidden(t){return this.hidden=t,this}use(t,...e){return t(this,...e),this}}},81653:(t,e,s)=>{function n(t,e){return Object.fromEntries(Object.entries(t).map((([t,s])=>[t,e(s)])))}s.d(e,{Q:()=>n})}}]);
//# sourceMappingURL=83.bb1920d2.js.map