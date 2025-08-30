import React, { useState } from 'react';
import { useNavigate, Navigate } from 'react-router-dom';
import {
  Box,
  Card,
  CardContent,
  TextField,
  Button,
  Typography,
  Alert,
  Container,
} from '@mui/material';
import { useAuth } from '../context/AuthContext';
import { loginStyles } from '../styles/pages/loginStyles';

const Login: React.FC = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  
  const { user, login } = useAuth();
  const navigate = useNavigate();

  // Redirect if already logged in
  if (user) {
    return <Navigate to="/" replace />;
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      await login(username, password);
      navigate('/');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Container sx={loginStyles.container}>
      <Card>
        <CardContent sx={loginStyles.cardContent}>
          <Box sx={loginStyles.headerContainer}>
            <Typography variant="h4" component="h1" gutterBottom>
              eBay Manager
            </Typography>
            <Typography variant="body1" color="textSecondary">
              Sign in to manage your eBay accounts
            </Typography>
          </Box>

          {error && (
            <Alert severity="error" sx={loginStyles.errorAlert}>
              {error}
            </Alert>
          )}

          <Box component="form" onSubmit={handleSubmit}>
            <TextField
              fullWidth
              label="Username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              margin="normal"
              required
              autoFocus
            />
            
            <TextField
              fullWidth
              label="Password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              margin="normal"
              required
            />

            <Button
              type="submit"
              fullWidth
              variant="contained"
              size="large"
              disabled={loading}
              sx={loginStyles.loginButton}
            >
              {loading ? 'Signing in...' : 'Sign In'}
            </Button>
          </Box>

          <Box sx={loginStyles.demoContainer}>
            <Typography variant="body2" color="textSecondary">
              Demo credentials:
            </Typography>
            <Typography variant="body2">
              <strong>Admin:</strong> admin / admin123
            </Typography>
          </Box>
        </CardContent>
      </Card>
    </Container>
  );
};

export default Login;