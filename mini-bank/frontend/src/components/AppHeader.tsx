import { AppBar, Toolbar, Typography, Button, Box } from "@mui/material";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";

export function AppHeader() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  async function handleLogout() {
    await logout();
    navigate("/login");
  }

  return (
    <AppBar position="static" color="primary">
      <Toolbar>
        <Typography variant="h6" sx={{ flexGrow: 1, fontWeight: 700 }}>
          mini-bank
        </Typography>
        {user && (
          <Box display="flex" alignItems="center" gap={2}>
            <Typography variant="body2">
              {user.full_name} ({user.role === "customer" ? "klient" : user.role === "supervisor" ? "supervisor" : "agent"})
            </Typography>
            <Button color="inherit" onClick={handleLogout}>
              Wyloguj
            </Button>
          </Box>
        )}
      </Toolbar>
    </AppBar>
  );
}
