import { useState, useEffect, useRef } from "react";
import { Search, FileText, Briefcase, Users, Loader2 } from "lucide-react";
import { Input } from "@/components/ui/input";
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from "@/components/ui/command";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api";
import { formatIST } from "@/utils/timezone";

interface SearchResult {
  id: number;
  type: "project" | "case_study" | "user";
  title: string;
  subtitle?: string;
  metadata?: string;
}

export function GlobalSearch() {
  const [open, setOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const navigate = useNavigate();
  const inputRef = useRef<HTMLInputElement>(null);

  const { data: searchResults, isLoading } = useQuery({
    queryKey: ["globalSearch", searchQuery],
    queryFn: () => apiClient.globalSearch(searchQuery),
    enabled: searchQuery.length >= 2 && open,
    retry: false,
  });

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        setOpen(true);
        setTimeout(() => inputRef.current?.focus(), 100);
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  const handleSelect = (result: SearchResult) => {
    setOpen(false);
    setSearchQuery("");
    
    switch (result.type) {
      case "project":
        navigate(`/insights?project_id=${result.id}`);
        break;
      case "case_study":
        navigate(`/case-studies?view=${result.id}`);
        break;
      case "user":
        // Navigate to user profile if needed
        break;
    }
  };

  const getIcon = (type: string) => {
    switch (type) {
      case "project":
        return <Briefcase className="h-4 w-4" />;
      case "case_study":
        return <FileText className="h-4 w-4" />;
      case "user":
        return <Users className="h-4 w-4" />;
      default:
        return <Search className="h-4 w-4" />;
    }
  };

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <div className="relative w-full max-w-md">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            ref={inputRef}
            placeholder="Search projects, case studies... (Ctrl+K)"
            className="w-full bg-muted/50 pl-9 pr-9"
            value={searchQuery}
            onChange={(e) => {
              setSearchQuery(e.target.value);
              if (e.target.value.length >= 2) {
                setOpen(true);
              }
            }}
            onFocus={() => {
              if (searchQuery.length >= 2) {
                setOpen(true);
              }
            }}
          />
          {searchQuery && (
            <kbd className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none hidden h-5 select-none items-center gap-1 rounded border bg-muted px-1.5 font-mono text-[10px] font-medium opacity-100 sm:flex">
              <span className="text-xs">⌘</span>K
            </kbd>
          )}
        </div>
      </PopoverTrigger>
      <PopoverContent className="w-[400px] p-0" align="start">
        <Command shouldFilter={false}>
          <CommandInput
            placeholder="Search projects, case studies..."
            value={searchQuery}
            onValueChange={setSearchQuery}
          />
          <CommandList>
            {isLoading ? (
              <div className="flex items-center justify-center p-6">
                <Loader2 className="h-4 w-4 animate-spin" />
              </div>
            ) : !searchQuery || searchQuery.length < 2 ? (
              <CommandEmpty>Type at least 2 characters to search</CommandEmpty>
            ) : !searchResults || searchResults.length === 0 ? (
              <CommandEmpty>No results found</CommandEmpty>
            ) : (
              <>
                <CommandGroup heading="Projects">
                  {searchResults
                    .filter((r: SearchResult) => r.type === "project")
                    .map((result: SearchResult) => (
                      <CommandItem
                        key={`project-${result.id}`}
                        onSelect={() => handleSelect(result)}
                        className="flex items-center gap-3"
                      >
                        {getIcon(result.type)}
                        <div className="flex-1">
                          <p className="text-sm font-medium">{result.title}</p>
                          {result.subtitle && (
                            <p className="text-xs text-muted-foreground">
                              {result.subtitle}
                            </p>
                          )}
                          {result.metadata && (
                            <p className="text-xs text-muted-foreground">
                              {result.metadata}
                            </p>
                          )}
                        </div>
                      </CommandItem>
                    ))}
                </CommandGroup>
                <CommandGroup heading="Case Studies">
                  {searchResults
                    .filter((r: SearchResult) => r.type === "case_study")
                    .map((result: SearchResult) => (
                      <CommandItem
                        key={`case-${result.id}`}
                        onSelect={() => handleSelect(result)}
                        className="flex items-center gap-3"
                      >
                        {getIcon(result.type)}
                        <div className="flex-1">
                          <p className="text-sm font-medium">{result.title}</p>
                          {result.subtitle && (
                            <p className="text-xs text-muted-foreground">
                              {result.subtitle}
                            </p>
                          )}
                        </div>
                      </CommandItem>
                    ))}
                </CommandGroup>
              </>
            )}
          </CommandList>
        </Command>
      </PopoverContent>
    </Popover>
  );
}

