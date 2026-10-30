import React, { useState, useEffect, useMemo } from "react";
import {
  X,
  ZoomIn,
  ZoomOut,
  Filter,
  Users,
  MapPin,
  Calendar,
  Info,
  Share2,
  ExternalLink,
  BookOpen
} from "lucide-react";
import { api } from "../services/api";
import { LifeGraphData, GraphNode, PeopleAndPlacesData, PersonEntity, PlaceEntity } from "../types";

interface LifeGraphModalProps {
  isOpen: boolean;
  onClose: () => void;
  initialTab?: "graph" | "people" | "places";
}

export const LifeGraphModal: React.FC<LifeGraphModalProps> = ({
  isOpen,
  onClose,
  initialTab = "graph"
}) => {
  if (!isOpen) return null;

  const [activeTab, setActiveTab] = useState<"graph" | "people" | "places">(initialTab);
  const [graphData, setGraphData] = useState<LifeGraphData | null>(null);
  const [entitiesData, setEntitiesData] = useState<PeopleAndPlacesData | null>(null);
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const [filterType, setFilterType] = useState<string>("All");
  const [zoom, setZoom] = useState<number>(1);

  useEffect(() => {
    async function loadAllData() {
      try {
        const [graph, entities] = await Promise.all([
          api.getLifeGraph().catch(() => null),
          api.getPeopleAndPlaces().catch(() => null)
        ]);
        if (graph) setGraphData(graph);
        if (entities) setEntitiesData(entities);
      } catch (err) {
        console.error("Failed to load people & places data:", err);
      }
    }
    loadAllData();
  }, []);

  const getNodeColor = (type: string) => {
    switch (type.toLowerCase()) {
      case "user":
        return { bg: "#f59e0b", border: "#b45309", text: "#78350f" }; // amber
      case "person":
        return { bg: "#3b82f6", border: "#1d4ed8", text: "#1e3a8a" }; // blue
      case "place":
        return { bg: "#10b981", border: "#047857", text: "#064e3b" }; // emerald
      case "project":
        return { bg: "#8b5cf6", border: "#6d28d9", text: "#4c1d95" }; // purple
      case "commitment":
        return { bg: "#ef4444", border: "#b91c1c", text: "#7f1d1d" }; // red
      default:
        return { bg: "#6b7280", border: "#374151", text: "#1f2937" };
    }
  };

  // Dynamically compute node positions so no nodes ever overlap or get stacked!
  const computedPositions = useMemo(() => {
    const pos: Record<string, { x: number; y: number }> = {};
    if (!graphData?.nodes) return pos;

    // Center node for "You" / "User"
    pos["You"] = { x: 325, y: 210 };

    const nonRootNodes = graphData.nodes.filter((n) => n.label !== "You" && n.type !== "User");
    const total = nonRootNodes.length;

    nonRootNodes.forEach((node, index) => {
      const angle = (2 * Math.PI * index) / (total || 1) - Math.PI / 2;
      let radius = 135;
      if (node.type.toLowerCase() === "place") radius = 165;
      else if (node.type.toLowerCase() === "commitment") radius = 150;
      else if (node.type.toLowerCase() === "project") radius = 115;
      else if (node.type.toLowerCase() === "person") radius = 130;

      const offset = (index % 2 === 0 ? 1 : -1) * 15;
      const x = Math.round(325 + (radius + offset) * Math.cos(angle));
      const y = Math.round(210 + (radius + offset) * Math.sin(angle) * 0.85);

      pos[node.label] = {
        x: Math.max(50, Math.min(600, x)),
        y: Math.max(40, Math.min(380, y))
      };
    });

    return pos;
  }, [graphData]);

  const filteredNodes = useMemo(() => {
    return graphData?.nodes.filter((n) => {
      if (filterType === "All") return true;
      return n.type.toLowerCase() === filterType.toLowerCase();
    }) || [];
  }, [graphData, filterType]);

  const peopleList: PersonEntity[] = entitiesData?.people || [];
  const placesList: PlaceEntity[] = entitiesData?.places || [];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 backdrop-blur-xs p-4 sm:p-6 select-none animate-fadeIn">
      <div className="bg-[#fcf8f0] border-2 border-[#cfbeaa] rounded-2xl w-full max-w-5xl h-[88vh] shadow-2xl flex flex-col relative overflow-hidden">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 px-6 py-3.5 border-b border-[#e5d5be] bg-[#f5ecda]">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-[#80502c]/10 border border-[#80502c]/30 flex items-center justify-center text-[#80502c]">
              <Users className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-xl font-bold font-serif-title text-[#3a2514] flex items-center gap-2">
                <span>People & Places</span>
                <span className="text-xs font-normal px-2 py-0.5 rounded-full bg-[#ebdcc4] text-[#4d3319]">
                  Life Graph & Directory
                </span>
              </h3>
              <p className="text-xs text-[#705439]">
                Connections, shared moments, and geographical journeys extracted from your memories.
              </p>
            </div>
          </div>

          <div className="flex items-center justify-between sm:justify-end gap-2 w-full sm:w-auto">
            {/* View Tab Switcher */}
            <div className="flex items-center bg-[#ebdcc4] p-1 rounded-xl border border-[#d8c5aa] text-xs font-medium overflow-x-auto max-w-full">
              <button
                onClick={() => setActiveTab("graph")}
                className={`px-2.5 sm:px-3 py-1 rounded-lg transition-all cursor-pointer flex items-center gap-1.5 whitespace-nowrap ${
                  activeTab === "graph"
                    ? "bg-[#80502c] text-white shadow-xs font-semibold"
                    : "text-[#6b5038] hover:text-[#382312]"
                }`}
              >
                <Share2 className="w-3.5 h-3.5" />
                <span>Life Graph</span>
              </button>
              <button
                onClick={() => setActiveTab("people")}
                className={`px-2.5 sm:px-3 py-1 rounded-lg transition-all cursor-pointer flex items-center gap-1.5 whitespace-nowrap ${
                  activeTab === "people"
                    ? "bg-[#80502c] text-white shadow-xs font-semibold"
                    : "text-[#6b5038] hover:text-[#382312]"
                }`}
              >
                <Users className="w-3.5 h-3.5" />
                <span>People ({peopleList.length})</span>
              </button>
              <button
                onClick={() => setActiveTab("places")}
                className={`px-2.5 sm:px-3 py-1 rounded-lg transition-all cursor-pointer flex items-center gap-1.5 whitespace-nowrap ${
                  activeTab === "places"
                    ? "bg-[#80502c] text-white shadow-xs font-semibold"
                    : "text-[#6b5038] hover:text-[#382312]"
                }`}
              >
                <MapPin className="w-3.5 h-3.5" />
                <span>Places ({placesList.length})</span>
              </button>
            </div>

            <button
              onClick={onClose}
              className="p-1.5 text-[#8c7155] hover:text-[#382312] rounded-lg hover:bg-black/5 transition-colors cursor-pointer shrink-0"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* TAB 1: LIFE GRAPH */}
        {activeTab === "graph" && (
          <div className="flex-1 flex flex-col relative overflow-hidden bg-[#fdfbf6]">
            {/* Subheader Controls */}
            <div className="px-6 py-2 bg-[#faf4e8] border-b border-[#ebdcc4] flex flex-wrap items-center justify-between gap-2 text-xs">
              <div className="flex items-center gap-1">
                <Filter className="w-3.5 h-3.5 text-[#8a6e50] mr-1" />
                <span className="text-[11px] text-[#8a6e50] mr-1 font-medium">Filter:</span>
                {["All", "Person", "Place", "Project", "Commitment"].map((t) => (
                  <button
                    key={t}
                    onClick={() => setFilterType(t)}
                    className={`px-2.5 py-0.5 rounded-full transition-all cursor-pointer ${
                      filterType === t
                        ? "bg-[#80502c] text-white font-medium"
                        : "bg-white/70 text-[#73563a] hover:bg-white border border-[#e0cfba]"
                    }`}
                  >
                    {t}
                  </button>
                ))}
              </div>

              {/* Zoom Controls */}
              <div className="flex items-center gap-1 bg-white/70 px-2 py-0.5 rounded-lg border border-[#d8c5aa]">
                <button
                  onClick={() => setZoom((z) => Math.max(0.6, z - 0.15))}
                  className="p-1 text-[#8a6e50] hover:text-[#3d2714] cursor-pointer"
                  title="Zoom Out"
                >
                  <ZoomOut className="w-3.5 h-3.5" />
                </button>
                <span className="text-[11px] text-[#8a6e50] font-mono px-1">
                  {Math.round(zoom * 100)}%
                </span>
                <button
                  onClick={() => setZoom((z) => Math.min(1.8, z + 0.15))}
                  className="p-1 text-[#8a6e50] hover:text-[#3d2714] cursor-pointer"
                  title="Zoom In"
                >
                  <ZoomIn className="w-3.5 h-3.5" />
                </button>
                <button
                  onClick={() => setZoom(1)}
                  className="text-[10px] text-amber-800 hover:underline px-1 cursor-pointer"
                >
                  Reset
                </button>
              </div>
            </div>

            {/* SVG Graph Canvas */}
            <div className="flex-1 relative overflow-hidden flex items-center justify-center select-none bg-[radial-gradient(#e8dac1_1px,transparent_1px)] [background-size:16px_16px]">
              <svg
                className="w-full h-full cursor-grab active:cursor-grabbing"
                viewBox="0 0 650 420"
                style={{ transform: `scale(${zoom})`, transformOrigin: "center center" }}
              >
                <defs>
                  <marker
                    id="arrow"
                    viewBox="0 0 10 10"
                    refX="22"
                    refY="5"
                    markerWidth="6"
                    markerHeight="6"
                    orient="auto-start-reverse"
                  >
                    <path d="M 0 0 L 10 5 L 0 10 z" fill="#bfaea0" />
                  </marker>
                </defs>

                {/* Graph Edges */}
                {graphData?.edges.map((edge) => {
                  const src = computedPositions[edge.source] || { x: 325, y: 210 };
                  const tgt = computedPositions[edge.target] || { x: 380, y: 260 };
                  const midX = (src.x + tgt.x) / 2;
                  const midY = (src.y + tgt.y) / 2;

                  return (
                    <g key={edge.id}>
                      <line
                        x1={src.x}
                        y1={src.y}
                        x2={tgt.x}
                        y2={tgt.y}
                        stroke="#c7b6a2"
                        strokeWidth="1.6"
                        strokeDasharray={edge.label === "requires" ? "4 3" : "none"}
                        markerEnd="url(#arrow)"
                      />
                      <rect
                        x={midX - 24}
                        y={midY - 7}
                        width="48"
                        height="14"
                        rx={4}
                        fill="#fbf7ee"
                        stroke="#e1d2be"
                        strokeWidth="0.8"
                      />
                      <text
                        x={midX}
                        y={midY + 3}
                        textAnchor="middle"
                        fontSize="8.5"
                        fill="#876d54"
                        fontFamily="sans-serif"
                        fontWeight="600"
                      >
                        {edge.label}
                      </text>
                    </g>
                  );
                })}

                {/* Graph Nodes */}
                {filteredNodes.map((node) => {
                  const pos = computedPositions[node.label] || { x: 325, y: 210 };
                  const colors = getNodeColor(node.type);
                  const isSelected = selectedNode?.id === node.id;
                  const isUser = node.type.toLowerCase() === "user" || node.label === "You";

                  return (
                    <g
                      key={node.id}
                      transform={`translate(${pos.x}, ${pos.y})`}
                      className="cursor-pointer transition-transform hover:scale-110"
                      onClick={() => setSelectedNode(node)}
                    >
                      <circle
                        r={isUser ? 26 : 19}
                        fill={colors.bg}
                        stroke={isSelected ? "#000000" : colors.border}
                        strokeWidth={isSelected ? 3.5 : 2}
                        filter="drop-shadow(0 2px 5px rgba(0,0,0,0.18))"
                      />
                      <text
                        textAnchor="middle"
                        dy=".3em"
                        fill="#ffffff"
                        fontSize={isUser ? 11 : 9.5}
                        fontWeight="bold"
                        fontFamily="sans-serif"
                      >
                        {node.label.slice(0, 10)}
                      </text>
                      <text
                        textAnchor="middle"
                        dy="2.4em"
                        fontSize="9.5"
                        fill="#523924"
                        fontWeight="600"
                        fontFamily="sans-serif"
                        className="bg-white/80"
                      >
                        {node.label}
                      </text>
                    </g>
                  );
                })}
              </svg>

              {/* Node Inspector Side Panel */}
              {selectedNode && (
                <div className="absolute right-4 bottom-4 w-72 bg-[#fdfbf7] p-4 rounded-xl border border-[#d8c5aa] shadow-xl text-xs">
                  <div className="flex items-center justify-between mb-2 pb-1.5 border-b border-[#eaddcd]">
                    <span className="font-bold text-[#3d2714] flex items-center gap-1.5">
                      <Info className="w-3.5 h-3.5 text-amber-700" />
                      {selectedNode.label}
                    </span>
                    <span
                      className="px-2 py-0.5 rounded text-[10px] text-white font-bold"
                      style={{ backgroundColor: getNodeColor(selectedNode.type).bg }}
                    >
                      {selectedNode.type}
                    </span>
                  </div>
                  <p className="text-[#6e543c] text-[11px] mb-2 leading-relaxed">
                    Connected entity in your personal life graph extracted by multimodal AI.
                  </p>
                  <div className="space-y-1 text-[11px] text-[#82664d] border-t border-[#eaddcd] pt-2">
                    <div>
                      Relationships:{" "}
                      <strong>
                        {graphData?.edges.filter(
                          (e) => e.source === selectedNode.label || e.target === selectedNode.label
                        ).length || 1} connected links
                      </strong>
                    </div>
                  </div>
                  <button
                    onClick={() => setSelectedNode(null)}
                    className="mt-3 w-full py-1 text-center bg-[#f0e4d2] hover:bg-[#e2d2ba] text-[#523924] rounded font-semibold text-[11px] cursor-pointer"
                  >
                    Close Inspector
                  </button>
                </div>
              )}
            </div>
          </div>
        )}

        {/* TAB 2: PEOPLE DIRECTORY */}
        {activeTab === "people" && (
          <div className="flex-1 p-6 overflow-y-auto bg-[#f8f3ea]">
            {peopleList.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-64 text-center p-6">
                <div className="w-12 h-12 rounded-full bg-[#ebdcc4] text-[#80502c] flex items-center justify-center mb-3">
                  <Users className="w-6 h-6" />
                </div>
                <h4 className="text-base font-bold text-[#352010] font-serif-title">No People Recorded Yet</h4>
                <p className="text-xs text-[#705439] max-w-sm mt-1">
                  Mention family, friends, and colleagues in your diary entries and LifeBook will automatically index them here.
                </p>
              </div>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-5">
                {peopleList.map((person) => (
                  <div
                    key={person.name}
                    className="bg-white rounded-xl p-4 border border-[#dbcbb6] shadow-sm hover:shadow-md transition-all flex flex-col justify-between relative group"
                  >
                    <div>
                      <div className="flex items-start justify-between mb-3">
                        <div className="flex items-center gap-3">
                          <div className="w-11 h-11 rounded-full bg-blue-100 border-2 border-blue-400 text-blue-900 flex items-center justify-center font-serif-title text-base font-bold shadow-xs">
                            {person.name.slice(0, 2).toUpperCase()}
                          </div>
                          <div>
                            <h4 className="text-sm font-bold text-[#352010] font-serif-title">
                              {person.name}
                            </h4>
                            <span className="text-[10px] text-blue-700 bg-blue-50 border border-blue-200 px-1.5 py-0.2 rounded font-medium">
                              {person.relationships[0] || "Friend"}
                            </span>
                          </div>
                        </div>
                        <span className="text-[11px] font-semibold text-[#80502c] bg-[#ebdcc4] px-2 py-0.5 rounded-full">
                          {person.count} {person.count === 1 ? "entry" : "entries"}
                        </span>
                      </div>

                      <div className="text-xs text-[#6e543c] space-y-1.5 mb-3 bg-[#faf5ec] p-2.5 rounded-lg border border-[#eddcc7]">
                        <div className="flex items-center justify-between text-[11px]">
                          <span className="text-[#8c7155]">Last Mentioned:</span>
                          <span className="font-medium text-[#422915]">{person.last_seen || "Recent"}</span>
                        </div>
                        <div className="flex items-center justify-between text-[11px]">
                          <span className="text-[#8c7155]">Role:</span>
                          <span className="font-medium text-[#422915]">
                            {person.relationships.join(", ")}
                          </span>
                        </div>
                      </div>

                      {person.memories && person.memories.length > 0 && (
                        <div className="space-y-1">
                          <span className="text-[10px] font-bold uppercase tracking-wider text-[#8a6849]">
                            Related Memories:
                          </span>
                          {person.memories.slice(0, 2).map((m) => (
                            <div
                              key={m.id}
                              className="text-[11px] text-[#4d3319] flex items-center gap-1.5 truncate"
                            >
                              <BookOpen className="w-3 h-3 text-[#8a6849] shrink-0" />
                              <span className="truncate">{m.title}</span>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>

                    <div className="mt-4 pt-2 border-t border-[#f0e3ce] flex items-center justify-between text-[11px] text-[#80502c]">
                      <span className="font-medium">In Life Graph</span>
                      <button
                        onClick={() => {
                          setActiveTab("graph");
                          const matched = graphData?.nodes.find((n) => n.label === person.name);
                          if (matched) setSelectedNode(matched);
                        }}
                        className="text-amber-900 font-semibold hover:underline flex items-center gap-1 cursor-pointer"
                      >
                        <span>View in Graph</span>
                        <ExternalLink className="w-3 h-3" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* TAB 3: PLACES DIRECTORY */}
        {activeTab === "places" && (
          <div className="flex-1 p-6 overflow-y-auto bg-[#f8f3ea]">
            {placesList.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-64 text-center p-6">
                <div className="w-12 h-12 rounded-full bg-[#ebdcc4] text-[#80502c] flex items-center justify-center mb-3">
                  <MapPin className="w-6 h-6" />
                </div>
                <h4 className="text-base font-bold text-[#352010] font-serif-title">No Places Recorded Yet</h4>
                <p className="text-xs text-[#705439] max-w-sm mt-1">
                  Locations and travel destinations mentioned in your diary or captured in photos will appear here.
                </p>
              </div>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-5">
                {placesList.map((place) => (
                  <div
                    key={place.name}
                    className="bg-white rounded-xl p-4 border border-[#dbcbb6] shadow-sm hover:shadow-md transition-all flex flex-col justify-between relative group"
                  >
                    <div>
                      {place.photos && place.photos.length > 0 ? (
                        <div className="aspect-16/9 rounded-lg overflow-hidden bg-[#1e140d] mb-3 border border-[#d5c2a7] relative">
                          <img
                            src={place.photos[0]}
                            alt={place.name}
                            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                            onError={(e) => {
                              (e.target as HTMLImageElement).src =
                                "https://images.unsplash.com/photo-1469854523086-cc02fe5d8800?w=400&auto=format&fit=crop&q=80";
                            }}
                          />
                          <span className="absolute bottom-1.5 left-1.5 px-2 py-0.5 rounded bg-black/60 text-white text-[10px] font-medium backdrop-blur-xs">
                            {place.photos.length} {place.photos.length === 1 ? "photo" : "photos"}
                          </span>
                        </div>
                      ) : (
                        <div className="h-16 rounded-lg bg-emerald-50 border border-emerald-200 flex items-center justify-center text-emerald-800 mb-3">
                          <MapPin className="w-6 h-6" />
                        </div>
                      )}

                      <div className="flex items-start justify-between mb-2">
                        <div>
                          <h4 className="text-sm font-bold text-[#352010] font-serif-title flex items-center gap-1.5">
                            <MapPin className="w-4 h-4 text-emerald-700" />
                            <span>{place.name}</span>
                          </h4>
                          <span className="text-[10px] text-emerald-800 bg-emerald-50 border border-emerald-200 px-1.5 py-0.2 rounded font-medium">
                            Geographical Location
                          </span>
                        </div>
                        <span className="text-[11px] font-semibold text-emerald-900 bg-emerald-100 px-2 py-0.5 rounded-full">
                          {place.count} {place.count === 1 ? "visit" : "visits"}
                        </span>
                      </div>

                      <div className="text-xs text-[#6e543c] space-y-1.5 mb-3 bg-[#faf5ec] p-2.5 rounded-lg border border-[#eddcc7]">
                        <div className="flex items-center justify-between text-[11px]">
                          <span className="text-[#8c7155]">Last Visited:</span>
                          <span className="font-medium text-[#422915]">{place.last_visited || "Recent"}</span>
                        </div>
                      </div>

                      {place.memories && place.memories.length > 0 && (
                        <div className="space-y-1">
                          <span className="text-[10px] font-bold uppercase tracking-wider text-[#8a6849]">
                            Memories here:
                          </span>
                          {place.memories.slice(0, 2).map((m) => (
                            <div
                              key={m.id}
                              className="text-[11px] text-[#4d3319] flex items-center gap-1.5 truncate"
                            >
                              <BookOpen className="w-3 h-3 text-[#8a6849] shrink-0" />
                              <span className="truncate">{m.title}</span>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>

                    <div className="mt-4 pt-2 border-t border-[#f0e3ce] flex items-center justify-between text-[11px] text-[#80502c]">
                      <span className="font-medium">In Life Graph</span>
                      <button
                        onClick={() => {
                          setActiveTab("graph");
                          const matched = graphData?.nodes.find((n) => n.label === place.name);
                          if (matched) setSelectedNode(matched);
                        }}
                        className="text-amber-900 font-semibold hover:underline flex items-center gap-1 cursor-pointer"
                      >
                        <span>View in Graph</span>
                        <ExternalLink className="w-3 h-3" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
