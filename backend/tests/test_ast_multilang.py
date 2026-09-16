import pytest
from app.services.parser.ast_parser import ASTParserEngine

def test_ast_javascript_typescript_parser():
    ts_code = """
import React, { useState, useEffect } from 'react';
import { fetchRepoData } from './api';

export interface UserProps {
    name: string;
    role: string;
}

export class UserManager extends BaseManager {
    constructor(props) {
        super(props);
    }
}

export const processUserData = async (users, filter) => {
    validateUsers(users);
    return users.filter(filter);
};

function renderDashboard(data) {
    displayMetrics(data);
    return true;
}
"""
    symbols = ASTParserEngine.parse_file("repo_ts", "App.tsx", ts_code, "TypeScript")
    names = [s.name for s in symbols]
    types = [s.symbol_type for s in symbols]

    assert "UserManager" in names
    assert "processUserData" in names
    assert "renderDashboard" in names
    assert "import" in types
    assert "class" in types
    assert "function" in types

def test_ast_go_parser():
    go_code = """
package main

import (
    "fmt"
    "net/http"
)

type ServerConfig struct {
    Port int
    Host string
}

type Router interface {
    Route(path string)
}

func (s *ServerConfig) StartServer(timeout int) error {
    fmt.Println("Server starting")
    return nil
}

func HandleRequest(w http.ResponseWriter, r *http.Request) {
    fmt.Fprintf(w, "OK")
}
"""
    symbols = ASTParserEngine.parse_file("repo_go", "main.go", go_code, "Go")
    names = [s.name for s in symbols]
    
    assert "ServerConfig" in names
    assert "Router" in names
    assert "StartServer" in names
    assert "HandleRequest" in names

def test_ast_rust_parser():
    rust_code = """
pub struct WorkspaceAgent {
    name: String,
    loc: usize,
}

pub enum AgentStatus {
    Pending,
    Running,
    Completed,
}

pub async fn analyze_codebase(path: &str, depth: usize) -> Result<(), Error> {
    println!("Analyzing");
    Ok(())
}
"""
    symbols = ASTParserEngine.parse_file("repo_rs", "lib.rs", rust_code, "Rust")
    names = [s.name for s in symbols]

    assert "WorkspaceAgent" in names
    assert "AgentStatus" in names
    assert "analyze_codebase" in names

def test_ast_cpp_parser():
    cpp_code = """
#include <iostream>
#include <string>

class CodeIndexer {
public:
    void index_directory(std::string path);
    int calculate_metrics(int files);
};

void process_tokens(std::string token_stream) {
    std::cout << "Tokens" << std::endl;
}
"""
    symbols = ASTParserEngine.parse_file("repo_cpp", "main.cpp", cpp_code, "C++")
    names = [s.name for s in symbols]

    assert "CodeIndexer" in names
    assert "process_tokens" in names
